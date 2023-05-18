FROM python:3.8

COPY project project

RUN pip install streamlit pandas

ENTRYPOINT ["streamlit", "run", "project/app.py"]