#backend
python -m pip install "psycopg[binary]"
email validation:pip install "pydantic[email]",
python -m pip install "pydantic[email]" 
install pyjwt:python -m pip install pyjwt  
install passlib with bycrypt support:python -m pip install "passlib[bycrypt]" 
Fast API's login form(to handle form data correctly):python -m pip install python-multipart
python -m uvicorn main:app --reload
create virtual environment:python -m venv venv
activate virtual environment: .\venv\Scripts\Activate.ps1
install required backend packages:pip install fastapi uvicorn sqlalchemy pydantic passlib bcrypt python-jose psycopg2-binary
start backend server:uvicorn main:app --reload --port 8000 
install yfinance & supporting data libraries:pip install yfinance pandas
python library for JSON Web Tokens: pip install python-jose[cryptograph]
