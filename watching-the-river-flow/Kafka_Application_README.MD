# Investment Application Using Apache Kafka

## Table of Contents

1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Installation](#installation)
   - [Installing Kafka](#installing-kafka)
   - [Installing Zookeeper](#installing-zookeeper)
4. [Configuration](#configuration)
5. [Running Kafka](#running-kafka)
6. [Kafka Topics](#kafka-topics)
7. [Running the Investment Application](#running-the-investment-application)

---

## Introduction

This README provides instructions for setting up Apache Kafka to be used in an investment application that performs real-time analytics and alerting based on financial market data.

---

## Requirements

- Linux/MacOS machine
- JDK 11 or higher
- Python 3.x
- Kafka
- Zookeeper

---

## Installation

### Installing Kafka

1. **Download the Kafka binaries from [here](https://kafka.apache.org/downloads).**
   
2. **Extract the binaries:**

    ```bash
    tar -xzf kafka_x.x.x.tgz
    ```

3. **Move the Kafka binaries to your desired location:**

    ```bash
    mv kafka_x.x.x /usr/local/kafka
    ```

### Installing Zookeeper

- Zookeeper is bundled with Kafka, so no separate installation is needed.

---

## Configuration

1. **Navigate to Kafka's config directory:**

    ```bash
    cd /usr/local/kafka/config
    ```

2. **Edit the `server.properties` file to change configurations if needed. For example, set a unique broker id:**

    ```properties
    broker.id=0
    ```

3. **Create a `.env` file in your investment application's root directory to store sensitive information like API keys.**

---

## Running Kafka

1. **Start Zookeeper:**

    ```bash
    cd /usr/local/kafka
    bin/zookeeper-server-start.sh config/zookeeper.properties
    ```

2. **Start Kafka:**

    ```bash
    cd /usr/local/kafka
    bin/kafka-server-start.sh config/server.properties
    ```

---

## Kafka Topics

Create a topic for your investment application:

```bash
bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic investment_topic
```

---

## Running the Investment Application

1. **Navigate to your application's root directory.**

2. **Run your investment application:**

    ```bash
    python investment_app.py
    ```

---

This should set you up with a running Kafka broker that you can use for your investment application project. Follow the application-specific README for further instructions on how to run the investment application itself.

---
