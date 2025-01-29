from flask_seeder import Seeder
from app import db
from app.models.user import User
from app import logger

class DemoSeeder(Seeder):
    def run(self):   
        print("dgfdsgfd")
        logger.info("dfdgdfgg")
        user = User(
            first_name="abc",
            primary_email="abc@gmail.com",
            primary_phone=9865435632
            )

        db.session.add(user)
        db.session.commit()
        print(f"User {user.name} added to the database.")
        