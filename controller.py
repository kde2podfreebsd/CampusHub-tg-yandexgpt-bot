import json
from pathlib import Path
from enum import Enum
from config import basedir
from config import bot


class TokenStatus(Enum):
    INSUFFICIENT_TOKENS = "Insufficient Tokens"
    SUCCESS = "Success"


class UserController:
    USERS_FILE = Path(f"{basedir}/users.json")
    CONFIG_FILE = Path(f"{basedir}/config.json")

    storage = {}

    chain_users = []

    @classmethod
    def create_user(cls, chat_id: int, prompt: str, tokens: int = 5):
        users_list = cls._load_users_list()

        existing_user = next((user for user in users_list if user["chat_id"] == chat_id), None)

        if existing_user:
            print("User with this chat_id already exists.")
            return

        user_data = {"chat_id": chat_id, "start_state": True, "tokens": tokens}
        users_list.append(user_data)
        cls._save_users_list(users_list)

        history_file = Path(f"{basedir}/chats/{chat_id}_history.json")
        if not history_file.exists():
            start_prompt = {"role": "system", "text": prompt}
            with open(history_file, "w", encoding="utf-8") as file:
                json.dump([start_prompt], file, ensure_ascii=False, indent=2)

    @classmethod
    def deduct_tokens(cls, chat_id: int, tokens_to_deduct: int = 1):
        users_list = cls._load_users_list()
        user_data = next((user for user in users_list if user["chat_id"] == chat_id), None)

        if user_data:
            current_tokens = user_data.get("tokens", 0)
            if current_tokens < tokens_to_deduct:
                return TokenStatus.INSUFFICIENT_TOKENS
            else:
                user_data["tokens"] -= tokens_to_deduct
                cls._save_users_list(users_list)
                return TokenStatus.SUCCESS
        else:
            return TokenStatus.INSUFFICIENT_TOKENS

    @classmethod
    def update_tokens(cls, chat_id: int, new_tokens: int):
        users_list = cls._load_users_list()
        user_data = next((user for user in users_list if user["chat_id"] == chat_id), None)

        if user_data:
            user_data["tokens"] = new_tokens
            cls._save_users_list(users_list)
            return TokenStatus.SUCCESS
        else:
            return TokenStatus.INSUFFICIENT_TOKENS

    @classmethod
    def get_token_count(cls, chat_id: int):
        users_list = cls._load_users_list()
        user_data = next((user for user in users_list if user["chat_id"] == chat_id), None)

        return user_data.get("tokens") if user_data else None

    @classmethod
    def update_start_state(cls, chat_id: int, new_start_state: bool):
        users_list = cls._load_users_list()
        user_data = next((user for user in users_list if user["chat_id"] == chat_id), None)

        if user_data:
            user_data["start_state"] = new_start_state
            cls._save_users_list(users_list)

    @classmethod
    def get_start_state(cls, chat_id: int):
        users_list = cls._load_users_list()
        user_data = next((user for user in users_list if user["chat_id"] == chat_id), None)

        return user_data.get("start_state") if user_data else None

    @classmethod
    def _load_users_list(cls):
        if cls.USERS_FILE.exists():
            with open(cls.USERS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        else:
            return []

    @classmethod
    def _save_users_list(cls, users_list):
        with open(cls.USERS_FILE, "w", encoding="utf-8") as file:
            json.dump(users_list, file, ensure_ascii=False, indent=2)

    def add_message_id(self, user_id, message_id):
        self.storage[int(user_id)] = message_id

    async def delete_message_id(self, user_id):
        user_id = int(user_id)
        if user_id in self.storage:
            if self.storage[user_id] is not None:
                await bot.delete_message(user_id, self.storage[user_id])
                self.storage[user_id] = None

    @classmethod
    def clear_message_history(cls, chat_id: int):
        history_file = Path(f"{basedir}/chats/{chat_id}_history.json")

        if history_file.exists():
            with open(history_file, "r", encoding="utf-8") as file:
                history_data = json.load(file)

            if len(history_data) > 1:
                new_history_data = [history_data[0]]

                with open(history_file, "w", encoding="utf-8") as file:
                    json.dump(new_history_data, file, ensure_ascii=False, indent=2)
        else:
            print(f"History file not found for chat_id {chat_id}")

    @classmethod
    def update_all_tokens(cls):
        users_list = cls._load_users_list()

        if UserController.CONFIG_FILE.exists():
            with open(UserController.CONFIG_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

        for user_data in users_list:
            user_data["tokens"] = data['token_per_day_limit']

        cls._save_users_list(users_list)

    @classmethod
    def get_all_chat_ids(cls):
        users_list = cls._load_users_list()
        return [user["chat_id"] for user in users_list]

    @classmethod
    def add_user_to_chain(cls, chat_id):
        cls.chain_users.append(chat_id)

    @classmethod
    def remove_user_from_chain(cls, chat_id):
        cls.chain_users.remove(chat_id)

    @classmethod
    def get_users_from_chain(cls):
        return cls.chain_users


if __name__ == "__main__":
    chat_id = 1231244
    UserController.create_user(chat_id)

    deduction_result = UserController.deduct_tokens(chat_id)
    print(deduction_result)

    update_result = UserController.update_tokens(chat_id, 7)
    print(update_result)

    token_count = UserController.get_token_count(chat_id)
    print(f"Token count: {token_count}")

    UserController.update_start_state(chat_id, False)

    start_state = UserController.get_start_state(chat_id)
    print(f"Start state: {start_state}")
