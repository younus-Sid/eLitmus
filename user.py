from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, Id, Name, Email, Password):
        self.id = Id
        self.name = Name
        self.email = Email
        self.password = Password

    @staticmethod
    def get(user_id, sql):
        db = sql.cursor()
        user = db.execute(
            "SELECT * FROM users WHERE Id = %s", (user_id,)
        )
        user = db.fetchone()
        if not user:
            return None

        user = User(
            Id=user[0], Name=user[1], Email=user[2], Password=user[3]
        )
        db.close()
        return user

    @staticmethod
    def create(Id, Name, Email, Password, sql):
        db = sql.cursor()
        db.execute(
            "INSERT INTO users (Id, Name, Email, Password) VALUES (%s, %s, %s, %s)",
            (Id, Name, Email, Password),
        )
        sql.commit()
        db.close
