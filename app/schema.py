instructions = [
    'DROP TABLE IF EXISTS users;',
    """
        CREATE TABLE users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name TEXT NOT NULL,
            surname TEXT,
            user TEXT NOT NULL,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            password TEXT NOT NULL,
            creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """,
    'INSERT INTO users (name, surname, user, password) values ("admin", "admin", "admin", "pbkdf2:sha256:260000$Jkd4rNsSI132MoDq$cff40255e53dbbea624e40eb8008bfaee5a318fcacbc6e4b0316a78f66cf9131");',
    'DROP TABLE IF EXISTS employees;',
    """
        CREATE TABLE employees (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name TEXT NOT NULL,
            surname TEXT,
            date DATE NOT NULL,
            observation TEXT,
            instagram_account TEXT,
            facebook_account TEXT,
            active TEXT,
            creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """,
    'DROP TABLE IF EXISTS instagram;',
    """
        CREATE TABLE instagram (
            employee_id INT,
            InputUrl TEXT,
            Url TEXT,
            Type TEXT,
            ShortCode TEXT,
            Caption TEXT,
            Hashtags TEXT,
            Mentions TEXT,
            CommentsCount INT,
            FirstComment TEXT,
            LatestComments TEXT,
            DimensionsHeight​ INT,
            DisplayUrl TEXT,
            Images TEXT,
            AltText TEXT,
            LikesCount INT,
            Timestamp DATETIME,
            ChildPosts​ TEXT,
            OwnerFullName TEXT,
            OwnerUsername TEXT,
            OwnerId INT,
            creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        );
    """,
    'DROP TABLE IF EXISTS posts;',
    """
        CREATE TABLE posts (
            employee_id INT NOT NULL,
            ShortCode TEXT NOT NULL,
            Description TEXT,
            Score INT,
            creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """,
    'DROP TABLE IF EXISTS tasks;',
    """
        CREATE TABLE tasks (
            employee_id INT NOT NULL,
            instagram_last_post DATETIME,
            facebook_last_post DATETIME,
            creation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        );
    """


]