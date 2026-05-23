import requests
import os
from pendulum import datetime
from airflow.decorators import dag, task
from airflow.models.baseoperator import chain
from airflow.models import Variable
from airflow.operators.python import get_current_context
from airflow.sensors.base import PokeReturnValue
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

@dag(
    start_date=datetime(2026, 3, 1),
    schedule='@daily',
    catchup=False, # Tránh chạy dồn dập nếu bạn chưa sẵn sàng dữ liệu quá khứ
    tags=['bybit', 'crypto'],
    template_searchpath=['/opt/airflow/dags/sql']
)
def bybit_pipeline():
    def get_conf():
        context = get_current_context()
        bybit = Variable.get('bybit', deserialize_json=True)
        return {
            'url': bybit['url'],
            'product': bybit['product'],
            'date': context['ds'],
            'date_nodash': context['ds_nodash'],
            'storage': Variable.get('data_storage')
        }

    @task.sensor(mode='reschedule', poke_interval=60, timeout=600)
    def wait_for_file() -> PokeReturnValue:
        conf = get_conf()
        # Chỉ check HEAD để xem file có trên server chưa, không tải về
        file_url = f"{conf['url']}/{conf['product']}/{conf['product']}{conf['date']}.csv.gz"
        r = requests.head(file_url)
        return PokeReturnValue(is_done=(r.status_code == 200))

    @task(retries=3)
    def download_data():
        conf = get_conf()
        local_path = f"{conf['storage']}/temp/{conf['product']}{conf['date']}.csv.gz"
        file_url = f"{conf['url']}/{conf['product']}/{conf['product']}{conf['date']}.csv.gz"
        
        # Tạo thư mục temp nếu chưa có
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_path

    transform_load_data = SparkSubmitOperator(
        task_id='spark_transform',
        conn_id='spark_master',
        application='/opt/spark/jobs/transform_load_spark.py',
        packages='org.postgresql:postgresql:42.6.0',
        application_args=[
            '--input', '{{ var.value.data_storage }}/temp/{{ var.json.bybit.product }}{{ ds }}.csv.gz',
            '--output_raw', '{{ var.value.data_storage }}/raw/{{ var.json.bybit.product }}/{{ ds }}',
            '--output_db', 'staging.{{ var.json.bybit.product }}{{ ds_nodash }}'
        ]
    )

    create_staging_schema = SQLExecuteQueryOperator(
        task_id='create_staging_schema',
        conn_id='postgres_ohlcv',
        sql='create_staging_schema.sql'
    )

    upsert_db = SQLExecuteQueryOperator(
        task_id='upsert_to_core',
        conn_id='postgres_ohlcv',
        sql='upsert_drop_postgres.sql'
    )

    @task.bash
    def cleanup():
        conf = get_conf()
        return f"rm {conf['storage']}/temp/{conf['product']}{conf['date']}.csv.gz"

    # Dòng chảy logic (Sequential flow để đảm bảo an toàn dữ liệu)
    chain(
        wait_for_file(),
        download_data(),
        create_staging_schema,
        transform_load_data,
        upsert_db,
        cleanup()
    )

bybit_pipeline()