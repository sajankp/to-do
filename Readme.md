
# FastTodo: A Powerful Todo Application Built with FastAPI and MongoDB
## Introduction

Welcome to my FastAPI MongoDB todo application! In this project, I am excited to leverage the power of FastAPI and MongoDB to build a robust and scalable web application specifically designed for managing todos. While I am relatively new to these technologies, I am eager to learn and grow as a developer, and I'm thrilled to share my progress with you.

Throughout the development process, I have been utilizing an AI assistant called ChatGPT to enhance my learning experience and streamline my development tasks. ChatGPT has been an invaluable resource, providing me with code suggestions, assisting in problem-solving, and guiding me through the intricacies of FastAPI, MongoDB, and todo application development.

## Technologies Used
This project primarily revolves around three key technologies:

**FastAPI**: FastAPI is a modern, fast (high-performance), web framework for building APIs with Python. It offers an intuitive and efficient way to develop web applications, leveraging the power of asynchronous programming.

**MongoDB**: MongoDB is a NoSQL document database that provides scalability, flexibility, and ease of use. It allows for seamless data storage and retrieval, making it an ideal choice for this application's data management needs.

**Docker**: Docker is a platform that allows you to automate the deployment of applications inside containers. It provides a consistent and reproducible environment, making it easier to package and deploy applications.

## Learning Process
Throughout this project, I have embraced a proactive learning approach to familiarize myself with FastAPI, MongoDB, and Docker. I have explored official documentation, gone through forums, and engaged in hands-on coding exercises. This iterative learning process has not only deepened my understanding but also sharpened my problem-solving skills.

To accelerate my learning journey, I have integrated ChatGPT into my development workflow. ChatGPT has served as an AI-powered assistant, providing me with helpful insights, answering my questions, and assisting me in overcoming challenges specific to this application development. This collaboration with ChatGPT has allowed me to learn and adapt more efficiently, making the most of emerging technologies in my project development.

## Benefits of AI Assistant Integration
The integration of an AI assistant like ChatGPT has brought numerous advantages to this project. Some notable benefits include:

* Accelerated Learning: ChatGPT has expedited my learning process by providing real-time guidance and recommendations, enabling me to quickly grasp complex concepts related to FastAPI, MongoDB, Docker, and todo list management.
* Enhanced Productivity: By leveraging ChatGPT's code suggestions and problem-solving capabilities, I have been able to streamline development tasks specific to todo application features, saving time and effort.

By combining the power of FastAPI, MongoDB, Docker, and ChatGPT, I am confident that this application will deliver a seamless user experience for managing todo lists while showcasing my ability to adapt to new technologies and leverage innovative solutions.

## Setting Up the Project

You can set up the FastAPI MongoDB todo application using either Docker or a virtual environment. Follow the appropriate steps below:

### 1. Install Docker (If Using Docker)
   - Make sure you have Docker installed on your machine. If not, you can download and install Docker from the official Docker website: [https://www.docker.com/get-started](https://www.docker.com/get-started)

### 2. Clone the Repository
   - Clone the repository to your local machine by running the following command in your terminal or command prompt:
     ```
     git clone https://github.com/sajankp/to-do
     ```

### 3. Navigate to the Project Directory
   - Navigate to the project directory using the following command:
     ```
     cd to-do
     ```

### 4. Create a Copy of .env.example with Configurations
   - Create a copy of the `.env.example` file in the repository and update it with the necessary configurations:
     ```
     cp .env.example .env
     ```
     Update the `.env` file as required.

### 5. (Optional) Set Up a Virtual Environment
If you prefer not to use Docker, you can set up the project using a virtual environment. This method keeps your dependencies isolated and ensures a clean Python environment.

#### 5.1 Install `venv`
   - If you don't already have `venv` installed, you can install it using the following command:
     ```
     python3 -m pip install --user virtualenv
     ```

#### 5.2 Create a Virtual Environment
   - Create a virtual environment in the project directory:
     ```
     python3 -m venv env
     ```

#### 5.3 Activate the Virtual Environment
   - Activate the virtual environment using the following command:
     - On macOS/Linux:
       ```
       source env/bin/activate
       ```
     - On Windows:
       ```
       .\env\Scripts\activate
       ```

#### 5.4 Install Project Dependencies
   - With the virtual environment activated, install the project dependencies listed in `requirements.txt`:
     ```
     pip install -r requirements.txt
     ```

### 6. Build the Docker Image (If Using Docker)
   - Build the Docker image using the following command:
     ```
     docker build -t todo .
     ```
     This command will build the Docker image based on the provided Dockerfile.

### 7. Run the Docker Container (If Using Docker)
   - Run the Docker container using the following command:
     ```
     docker run -p 80:80 todo
     ```
     This command will start the Docker container and map port 8000 of the container to port 8000 of your local machine.

### 8. Run the Application (If Using Virtual Environment)
   - If you are using a virtual environment, start the FastAPI application with the following command:
     ```
     uvicorn app.main:app --reload --port=80
     ```
     This command will start the FastAPI application and allow you to interact with it at [http://localhost/docs](http://localhost:8000/docs).

### 9. Access the Application
   - Once the application is running (either via Docker or a virtual environment), you can access it by opening your web browser and navigating to [http://localhost/docs](http://localhost:8000/docs) to test things out.

### 10. Run Tests Locally
Once the application is set up and running locally, you can run tests to ensure everything is functioning as expected.

#### Steps to Run Tests:
1. Make sure you are in the project root directory:
   ```bash
   cd to-do
   ```

2. If you are using a virtual environment, ensure it is activated:
   - On macOS/Linux:
     ```bash
     source env/bin/activate
     ```
   - On Windows:
     ```bash
     .\env\Scripts\activate
     ```

3. Run tests using `pytest`:
   ```bash
   pytest
   ```
   This will execute all the tests defined in the `tests/` directory and provide a report of the results.

4. To check the test coverage, use the following command:
   ```bash
   pytest --cov=app
   ```
   This will generate a coverage report, showing which parts of the code are covered by the tests.

#### Troubleshooting Tests:
- If any tests fail, review the error messages in the output to diagnose and fix issues.
- Ensure that your `.env` file is configured correctly and that the database is accessible for integration tests.

That's it! You have successfully set up the FastAPI MongoDB todo application using either Docker or a virtual environment. You can now explore and interact with the application through your web browser.

If you encounter any issues during the setup process, please refer to the project's documentation or feel free to reach out for assistance.

**References:**
- Docker Documentation: [https://docs.docker.com](https://docs.docker.com)
