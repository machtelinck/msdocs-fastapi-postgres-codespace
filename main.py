from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd
import Levenshtein

DATABASE_URL = "postgresql://admin:LocalPasswordOnly@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/verify_cp_ville_rue/")
async def verify_cp_ville_rue(code_postal: int, nom_commune: str, nom_rue: str, db: Session = Depends(get_db)):
    try:
        # Vérifier l'existence du couple code postal-ville
        sql_couple_exists = """
            SELECT EXISTS (
                SELECT 1 FROM cp_ville
                WHERE code_postal = :code_postal
                AND LOWER(nom_commune) = LOWER(:nom_commune)
            )
        """
        couple_exists = db.execute(text(sql_couple_exists), {"code_postal": code_postal, "nom_commune": nom_commune.lower()}).scalar()
        
        # Recherche de toutes les rues pour la combinaison code postal et ville
        sql_rues = """
            SELECT nom_afnor FROM cp_ville_rue
            WHERE code_postal = :code_postal
            AND LOWER(nom_commune) = LOWER(:nom_commune)
        """
        rues_result = db.execute(text(sql_rues), {"code_postal": code_postal, "nom_commune": nom_commune.lower()}).fetchall()
        rues_df = pd.DataFrame(rues_result, columns=['nom_afnor'])

       
        rue_exists = nom_rue.lower() in rues_df['nom_afnor'].str.lower().values
        
        if rue_exists:
            return {"message": "La rue existe pour le code postal et la ville donnés.", "couple_cp_ville_existe": couple_exists}
        else:
 
            if not rues_df.empty:
                first_street = rues_df.iloc[0]['nom_afnor']
                return {
                    "message": "La rue spécifiée n'existe pas pour le couple code postal-ville donné.",
                    "couple_cp_ville_existe": couple_exists,
                    "première_rue_suggestion": first_street
                }
            else:
                return {
                    "message": "Aucune rue trouvée pour le couple code postal-ville spécifié.",
                    "couple_cp_ville_existe": couple_exists
                }
    except Exception as e:
        print(f"Erreur : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


