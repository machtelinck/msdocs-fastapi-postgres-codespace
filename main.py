from sqlalchemy import Column, BigInteger, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import os
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, HTTPException, Depends
import os
from sqlalchemy import text
from sqlalchemy import create_engine, Column, BigInteger, String, and_

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://admin:LocalPasswordOnly@localhost:5432/postgres"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, bind=engine)
Base = declarative_base()


class CPVille(Base):
    __tablename__ = "cp_ville"
    code_postal = Column(BigInteger, primary_key=True)
    nom_commune = Column(String, primary_key=True)


app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/test_cp_ville/")
async def test_cp_ville(db: Session = Depends(get_db)):
    try:
        # Exécute une requête SQL brute pour récupérer simplement la première ligne
        result = db.execute(text("SELECT * FROM cp_ville LIMIT 1")).fetchone()
        if result:
            # Convertit le résultat en dict de manière sûre
            result_dict = {key: value for key, value in result._mapping.items()}
            return result_dict
        else:
            return {"message": "La table cp_ville est vide."}
    except Exception as e:
        print(f"Erreur de base de données : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")


@app.get("/verify_cp_ville/")
async def verify_cp_ville(code_postal: int, nom_commune: str, db: Session = Depends(get_db)):
    try:
        query = text("SELECT * FROM cp_ville")
        results = db.execute(query).fetchall()
        
        # Préparation des clés pour accéder aux valeurs dans les résultats
        key_code_postal = "('code_postal', '')"
        key_nom_commune = "('nom_commune', '')"
        
        # Filtrage des résultats en fonction de code_postal et nom_commune
        filtered_results = []
        for row in results:
            row_dict = {key: value for key, value in row._mapping.items()}
            if row_dict[key_code_postal] == code_postal and row_dict[key_nom_commune].strip().lower() == nom_commune.strip().lower():
                filtered_results.append(row_dict)
        
        if filtered_results:
            return {"message": "Résultats trouvés :", "data": filtered_results}
        else:
            return {"message": "Erreur : Aucun résultat trouvé pour les critères spécifiés."}
    except Exception as e:
        print(f"Erreur de base de données : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")



@app.get("/")
def read_root():
    return {"Hello": "Bienvenue sur mon API FastAPI!"}
