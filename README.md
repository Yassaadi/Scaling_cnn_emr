# Scaling_cnn_emr

# Yassine Assaadi: Deployment and scaling of Mobilenetv2 model

# Table of Contents:

Introduction
1.1 Problem Statement
1.2 Objectives in this Project
1.3 Project Workflow
Selected General Technical Choices
2.1 Distributed Computing
2.2 Transfer Learning
Deployment of the Solution Locally
3.1 Working Environment
3.2 Spark Installation
3.3 Package Installation
3.4 Library Import
3.5 Definition of Paths for Loading Images and Saving Results
3.6 Creating the SparkSession
3.7 Data Processing
3.7.1 Loading Data
3.7.2 Model Preparation
3.7.3 Definition of the Image Loading Process and Application
of Feature Extraction Using pandas UDF
3.7.4 Execution of Feature Extraction Actions
3.8 Loading Saved Data and Result Validation
Deployment of the Solution in the Cloud
4.1 Cloud Provider Choice: AWS
4.2 Technical Solution Choice: EMR
4.3 Data Storage Solution Choice: Amazon S3
4.4 Environment Configuration
4.5 Uploading Data to S3
4.6 Configuring the EMR Server
4.6.1 Step 1: Software and Steps
4.6.1.1 Software Configuration
4.6.1.2 Modifying Software Parameters
4.6.2 Step 2: Hardware
4.6.3 Step 3: General Cluster Settings
4.6.3.1 General Options
4.6.3.2 Bootstrap Actions
4.6.4 Step 4: Security
4.6.4.1 Security Options
4.7 Instantiating the Server
4.8 Creating an SSH Tunnel to the EC2 Instance (Master)
4.8.1 Creating Permissions for Incoming Connections
4.8.2 Creating SSH Tunnel to the Driver
4.8.3 Configuring FoxyProxy
4.8.4 Accessing EMR Server Applications via SSH Tunnel
4.9 Connecting to JupyterHub Notebook
4.10 Code Execution
4.10.1 Starting the Spark Session
4.10.2 Package Installation
4.10.3 Library Import
4.10.4 Definition of Paths for Loading Images and Saving Results
4.10.5 Data Processing
4.10.5.1 Loading Data
4.10.5.2 Model Preparation
4.10.5.3 Definition of the Image Loading Process
and Application of Feature Extraction Using pandas UDF
4.10.5.4 Execution of Feature Extraction Actions
4.10.6 Loading Saved Data and Result Validation
4.11 Tracking Task Progress with Spark History Server
4.12 Termination of EMR Instance
4.13 Cloning the EMR Server (if needed)
4.14 S3 Server Directory Structure at the End of the Project
Conclusion

#Introduction
## 1.1 Problem Statement
The young AgriTech startup, named "Fruits!", is looking to offer innovative solutions for fruit harvesting. The company's goal is to preserve the biodiversity of fruits by enabling specific treatments for each fruit species through the development of intelligent harvesting robots. In order to gain recognition, the startup plans to initially provide the general public with a mobile application that allows users to take a photo of a fruit and obtain information about it. The startup believes that this application will raise awareness among the public about fruit biodiversity and serve as a first version of the fruit image classification engine. Furthermore, the development of the mobile application will help build an initial version of the required Big Data architecture.

## 1.2 Objectives in this Project
The objectives of this project are to develop an initial data processing pipeline that includes preprocessing and dimension reduction steps. It is important to consider that the volume of data will rapidly increase after the completion of this project. Therefore, the objectives include:

Deploying the data processing in a Big Data environment
Developing scripts in PySpark to perform distributed computing

## 2.1 Distributed Computing
The project statement requires us to develop scripts in PySpark to account for the rapid increase in data volume after project delivery.

To quickly and simply understand what PySpark is and how it works, we recommend reading this article: PySpark: All You Need to Know about the Python Library.

The beginning of the article states the following:
"When it comes to database processing in Python, the pandas library immediately comes to mind. However, when dealing with excessively large databases, calculations become too slow. Fortunately, there is another Python library, similar to pandas, that allows processing of very large amounts of data: PySpark. Apache Spark is an open-source framework developed by UC Berkeley's AMPLab, enabling the processing of massive databases using distributed computing, a technique that leverages multiple computing units distributed across clusters to reduce query execution time. Spark was developed in Scala and performs optimally in its native language. However, the PySpark library offers the ability to use Spark with the Python language while maintaining similar performance to Scala implementations. Therefore, PySpark is a good alternative to the pandas library when dealing with excessively large datasets that result in time-consuming calculations."

As we can see, PySpark is a way to communicate with Spark using the Python language. Spark, on the other hand, is a tool for managing and coordinating task execution on data across a group of computers. Spark (or Apache Spark) is an open-source in-memory distributed computing framework for processing and analyzing massive amounts of data.

Another highly informative and comprehensive article to understand how Spark works, as well as the role of Spark Sessions that we will use in this project, is available.

Here is an excerpt from the article:
"Spark applications consist of a driver (the 'driver process') and multiple executors ('executor processes'). It can be configured to act as an executor itself (local mode) or to use as many executors as required to process the application. Spark supports automatic scaling by configuring a minimum and maximum number of executors.

Spark Architecture Diagram

The driver (sometimes referred to as the 'Spark Session') distributes and schedules tasks among the different executors, which execute the tasks and enable distributed processing. It is responsible for executing code on the different machines.

Each executor is a separate Java Virtual Machine (JVM) process that can be configured with the number of CPUs and allocated memory. Only one task can process a data partition at a time."

In both the local and cloud environments, we will use Spark and leverage it through Python scripts using PySpark.

In the local version of our script, we will simulate distributed computing to validate that our solution works. In the cloud version, we will perform operations on a cluster of machines.

## 2.2 Transfer Learning
The project statement also requires us to create an initial data processing pipeline that includes preprocessing and dimensionality reduction.

It is also mentioned that it is not necessary to train a model at this stage.

We have decided to use a transfer learning solution.

Simply put, transfer learning involves utilizing the knowledge already acquired by a pre-trained model (in this case, MobileNetV2) and adapting it to our problem.

We will provide our images to the model and retrieve the second-to-last layer of the model. The last layer of the model is a softmax layer used for image classification, which is not required for this project.

The second-to-last layer corresponds to a reduced-dimensional vector (1,1,1280).

This will allow us to create an initial version of the engine for fruit image classification.

MobileNetV2 has been chosen for its fast execution, which is particularly suitable for processing large volumes of data, as well as the low dimensionality of the output feature vector (1,1,1280).

![Diapositive4](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/3a935511-e1d7-4272-9bd7-fa75cd67849c)
![Diapositive5](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/1a88b2aa-f260-4c50-81ea-3a9c0599cc45)
![Diapositive6](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/93b53cb4-c2fe-4cc7-8802-c59c7e73a1d9)
![Diapositive7](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/9836f2c9-07da-4890-aa15-606122faff47)
![Diapositive8](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/0cacc4e9-7e27-42d3-b74d-9628cd1c3dfd)
![Diapositive9](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/5e22febd-3387-401a-b090-02a26ee79f9b)
![Diapositive11](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/d7c4c9fc-b677-4e61-b15b-47686083bbac)
![Diapositive12](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/f306caae-6a44-4c77-baa3-425cb83718ef)
![Diapositive13](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/a2b04994-592d-4f5a-8540-b46a5500d469)
![Diapositive14](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/a6534e04-4589-419d-89a7-28cd58740871)
![Diapositive15](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/5f584d7f-c405-419b-9c50-2c7b61a45640)
![Diapositive16](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/37d5bafe-7eaa-4551-b0ab-2b2348b79279)
![Diapositive17](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/7e83e4f3-effa-4544-9772-ff686cde2076)
![Diapositive18](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/7defb4f5-ac93-44bf-b54b-7c0cef892c2f)
![Diapositive19](https://github.com/Yassaadi/Scaling_cnn_emr/assets/106546639/0c37fe9e-77f9-415a-a47c-7c4cb6781866)
