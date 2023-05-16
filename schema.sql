CREATE TABLE allanswers (
    Ansid Integer PRIMARY KEY AUTO_INCREMENT,
    Answer VARCHAR(100) NOT NULL
);

CREATE TABLE users (
    Id Integer PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL
);

CREATE TABLE useranalytics (
    Id INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Stagenum INT NOT NULL,
    Accuracy FLOAT NOT NULL,
    Mistakecount INT NOT NULL,
    Timetaken INT NOT NULL,
    Ownerid INT NOT NULL,
    FOREIGN KEY (Ownerid) REFERENCES users(Id)
);
