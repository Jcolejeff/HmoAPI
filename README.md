# HmoAppAPI

The backend API for the HMO App, A ticketing system.

## Setting up your development environment

### Pre-reqs

Python version >= 3.10.
MySQL >= 8.0

## Setup

1. Clone this repository

2. Move into the project root

3. Create a virtual environment.

```sh
   python3 -m venv .venv
```

2. Activate virtual environment.

```sh
    source .\env\Scripts\activate`
```

3. Install project dependencies `pip install -r requirements.txt`
4. Create a .env file by copying the .env.sample file

```sh
cp .env.sample .env
```

5. Create a MySQL database and copy the name in to the `DATABASE_NAME` variable in your .env file.

6. Start server.

```sh
sh uvicorn main:app --reload

```

<!--
## Testing

This project uses [Pytest](https://pytest.org) for testing.

To run the test suite, run `sh ./test.sh` from the project root. -->
