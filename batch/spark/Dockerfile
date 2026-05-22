# ==============================================================================
# STAGE 1: BASE IMAGE - Cài đặt Spark và dependencies chung
# ==============================================================================
FROM python:3.12-slim-bookworm AS base

# ARG (Build Arguments): Biến chỉ tồn tại TRONG quá trình BUILD image
# - Có thể override khi build: docker build --build-arg spark_version=3.5.9
# - KHÔNG tồn tại trong container khi chạy (khác với ENV)
# - Dùng để customize image mà không cần sửa Dockerfile
ARG spark_version=3.5.8
ARG hadoop_version=3
ARG jdk_version=17

# ENV (Environment Variables): Biến môi trường tồn tại KHI CHẠY container
# - Có thể truy cập từ bên trong container: echo $SPARK_HOME
# - Dùng ${spark_version} để reference ARG ở trên
 
ENV SPARK_HOME=/opt/spark
ENV SPARK_MASTER_HOST=spark-master
ENV SPARK_MASTER_PORT=7077
ENV PYSPARK_PYTHON=python

# RUN: Chạy lệnh Linux khi BUILD image (không phải khi chạy container)
# - && cho phép chain nhiều lệnh, nếu 1 lệnh fail thì dừng hết
# - \ để xuống dòng cho dễ đọc
RUN apt-get update -y && \
    # Cài đặt tools cần thiết:
    # - wget: download file từ internet
    # - procps: quản lý process (ps, top, kill)
    # - openjdk-17-jre-headless: Java Runtime để chạy Spark (không cần GUI)
    apt-get install -y wget procps openjdk-${jdk_version}-jre-headless && \
    # Xóa cache apt để giảm image size
    apt-get clean && \
    # Download Spark binary từ Apache mirror
    wget https://dlcdn.apache.org/spark/spark-${spark_version}/spark-${spark_version}-bin-hadoop3.tgz && \
    # Giải nén Spark vào /opt rồi chuẩn hóa đường dẫn về ${SPARK_HOME}
    tar -xf spark-${spark_version}-bin-hadoop3.tgz -C /opt/ && \
    mv /opt/spark-${spark_version}-bin-hadoop3 ${SPARK_HOME} && \
    # Tải PostgreSQL JDBC driver vào thư mục jars của Spark
    wget https://repo1.maven.org/maven2/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar -P ${SPARK_HOME}/jars && \
    # Xóa file tải về để tiết kiệm dung lượng
    rm spark-${spark_version}-bin-hadoop3.tgz && \
    # Tạo user 'user' với UID 1000, group 0 (root group cho OpenShift compatibility)
    useradd -m -u 1000 -g 0 user && \
    # Tạo thư mục data và logs trước khi hạ quyền user
    mkdir -p /opt/data ${SPARK_HOME}/logs && \
    # Chuyển ownership sang user:root_group để user có quyền ghi
    chown -R 1000:0 ${SPARK_HOME} /opt/data

# USER: Chuyển sang chạy lệnh với user thường (không phải root) - Best practice bảo mật
USER user

# WORKDIR: Set working directory - Giống như 'cd' trong Linux
WORKDIR ${SPARK_HOME}


# ==============================================================================
# STAGE 2: SPARK MASTER - Image cho Spark Master node
# ==============================================================================
FROM base AS spark-master

# ARG chỉ scope trong stage này (không kế thừa từ base)
ARG spark_master_web_ui=8080

# EXPOSE: Document port nào container sẽ lắng nghe (không thực sự open port)
# - Để thực sự map port cần dùng -p trong docker run hoặc ports trong docker-compose
EXPOSE ${spark_master_web_ui} ${SPARK_MASTER_PORT}

# CMD: Lệnh chạy KHI KHỞI ĐỘNG container (không phải khi build)
# - Khởi động Spark Master process và redirect output vào log file
CMD ["/bin/bash", "-c", "bin/spark-class org.apache.spark.deploy.master.Master >> logs/spark-master.out"]


# ==============================================================================
# STAGE 3: SPARK WORKER - Image cho Spark Worker nodes
# ==============================================================================
FROM base AS spark-worker

ARG spark_worker_web_ui=8081

EXPOSE ${spark_worker_web_ui}

# Khởi động Spark Worker và kết nối tới Master
# - spark://${SPARK_MASTER_HOST}:${SPARK_MASTER_PORT} = spark://spark-master:7077
CMD ["/bin/bash", "-c", "bin/spark-class org.apache.spark.deploy.worker.Worker spark://${SPARK_MASTER_HOST}:${SPARK_MASTER_PORT} >> logs/spark-worker.out"]