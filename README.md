# Bookstore Application

## Overview
This document provides an overview of the design decisions, AI algorithms used, and detailed instructions on how to run the Bookstore application, which is built using a microservice architecture.

## Design Decisions

### 1. Microservice Architecture
**Microservice Architecture:** 
- The application is divided into multiple microservices, each responsible for a specific functionality. This approach allows for better scalability, maintainability, and independent deployment of services. The primary microservices are:

  - **Book Service:** Manages book-related operations such as adding, updating,retrieving book information, generarting book summaries using openai API, adding the book to cart and placing order for out cart.It also provides a real time notifications endpoint to send real time update on user order status.
  - **Order Service:** Handles order-related operations including placing orders and updating order history by the admin and updating the inventory service about the current stock after ordr has been confirmed.
  - **User Service:** Manages user authentication and authorization using JWT tokens.
  - **Inventory Service:** Manages inventory-related operations such as updating stock levels after an order is been confirmed and sending message to the book service so always be in sync.

### 2. Choice of Framework
**Flask:** 
- Flask was chosen for its simplicity, ease of use, and extensive documentation. Each microservice is built as a separate Flask application, which helps in managing and scaling each service independently.

### 3. Database Management
**SQLAlchemy:**
- SQLAlchemy is used as the Object-Relational Mapper (ORM) for database interactions in each microservice. It provides a high-level abstraction over the database and supports various relational databases. This makes it easier to handle database operations without writing raw SQL queries.

### 4. Authentication
**JWT (JSON Web Tokens):**
- JWT is used for secure authentication across all microservices. It provides a way to securely transmit information between parties as a JSON object. Using JWT for authentication helps in maintaining a stateless application, as the token can be verified without storing session information on the server.

### 5. Real-time Notifications
**Socket.IO:**
- Socket.IO is implemented in the Notification Service to provide real-time notifications to users. It allows the server to push updates to the client instantly, which is essential for features like order status updates.

### 6. Message Brokering
**RabbitMQ:**
- RabbitMQ is used as the message broker. It helps in decoupling different parts of the application, enabling asynchronous communication and improving scalability. RabbitMQ ensures reliable message delivery and can handle a large number of messages.

### 7. AI-Powered Features
**OpenAI GPT-3.5:**
- OpenAI's GPT-3.5 model is used for AI-powered book summarization. This model provides advanced natural language processing capabilities, allowing the application to generate concise summaries of book content.

## AI Algorithms

### Book Summarization
- The book summarization feature uses the OpenAI GPT-3.5 model. The model is accessed via the OpenAI API, which generates a summary of the given book content.
- **Algorithm:**
  1. The book content is sent as a prompt to the OpenAI API.
  2. The GPT-3.5 model processes the text and generates a summary.
  3. The summary is returned to the user.

## Running the Application

### Prerequisites
- Docker
- Docker Compose

### Steps

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/your-repo/bookstore.git
    cd bookstore
    ```

2. **Build and Start the Application:**
    ```bash
    docker-compose up --build
    ```

3. **Access the RabbitMQ Management Interface:**
    - URL: `http://localhost:15672`
    - Username: `guest`
    - Password: `guest`

4. **Access the Flask Applications:**
    - Book Service:
        - URL: `http://localhost:5002`
        - To Initialize Migration:
            ```bash
            docker-compose exec book-service bash
            flask db init
            flask db migrate
            flask db upgrade
            ```
    - Order Service:
        - URL: `http://localhost:5003`
        - To Initialize Migration:
            ```bash
            docker-compose exec order-service bash
            flask db init
            flask db migrate
            flask db upgrade
            ```
    - Inventory Service:
        - URL: `http://localhost:5001`
        - To Initialize Migration:
            ```bash
            docker-compose exec inventory-service bash
            flask db init
            flask db migrate
            flask db upgrade
            ```

5. **Port for each services**
    - Book Service : 5002
    -  Order Service: 5003
    - Inventory service: 5001

### Microservices

#### Book Service
# Book Service API Documentation

This document provides an overview of the routes and methods available in the Book Service of the Flask application.

## Routes

### Get Single Book
- Method: `GET`
- Route: `/books/<int:book_id>`

### Add Book
- Method: `POST`
- Route: `/books`

### Update Book
- Method: `PUT`
- Route: `/books/<int:book_id>`

### Delete Book
- Method: `DELETE`
- Route: `/books/<int:book_id>`

### Summarize Book
- Method: `GET`
- Route: `/summarize-book/<int:book_id>`

## SocketIO Events

### Connect
- Event: `connect`

### Disconnect
- Event: `disconnect`


#### Order Service
This document outlines the routes and methods available in the Order Service of the Flask application.

## Routes

### Place Order
- Method: `POST`
- Route: `/order`

### Get All Orders
- Method: `GET`
- Route: `/orders`

### Get Single Order
- Method: `GET`
- Route: `/order/<uuid:order_id>`

### Get Order Status
- Method: `GET`
- Route: `/order/<uuid:order_id>/status`

### Update Order Status
- Method: `PATCH`
- Route: `/order/<uuid:order_id>/status`

#### Notification Service
- **Connect:** `connect`
- **Disconnect:** `disconnect`
- **Order Status Update:** `order_status`

### Error Handling
- Proper error handling is implemented at the API level using Flask's error handling mechanisms.
- Database transactions are wrapped in try-except blocks to handle exceptions and roll back transactions if needed.
- RabbitMQ message consumption is done in a separate thread to avoid blocking the main application.

### Scaling
- The application uses RabbitMQ for message brokering, which allows it to scale horizontally by adding more instances of each microservice.
- Docker Compose is used to orchestrate the application components, making it easy to scale and manage dependencies.

## Conclusion
This document provides a comprehensive overview of the Bookstore application's design, AI algorithms, and instructions to run the application. The use of Flask, SQLAlchemy, JWT, Socket.IO, RabbitMQ, and OpenAI's GPT-3.5 ensures a robust, scalable, and feature-rich application.
