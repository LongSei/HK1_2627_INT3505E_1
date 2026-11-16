from locust import HttpUser, between, task


class ListBooksUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def list_books(self):
        self.client.get("/books", name="GET /books")
