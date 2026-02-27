import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from db import get_conn
import joblib
import os

MODELS_DIR = "models_ml"
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)


class ModeloPrecaoCustos:
    def __init__(self, veiculo_id=None):
        self.veiculo_id = veiculo_id
        self.modelo = None
        self.scaler = StandardScaler()
        self.model_path = f"{MODELS_DIR}/custo_modelo_{veiculo_id}.pkl"
        self.scaler_path = f"{MODELS_DIR}/custo_scaler_{veiculo_id}.pkl"
    
    def carregar_dados(self):
        """Carrega histórico de combustível e manutenção"""
        conn = get_conn()
        
        combustivel_sql = """
            SELECT 
                DATE(data) as data,
                CAST(quilometragem AS REAL) as quilometragem,
                CAST(valor_total AS REAL) as valor_combustivel,
                CAST(litros AS REAL) as litros
            FROM combustivel
            WHERE veiculo_id = ?
            ORDER BY data ASC
        """
        
        manutencao_sql = """
            SELECT 
                DATE(data_manutencao) as data,
                CAST(COALESCE(valor_peca, 0) + COALESCE(mao_de_obra, 0) AS REAL) as valor_manutencao
            FROM manutencao
            WHERE veiculo_id = ?
            ORDER BY data_manutencao ASC
        """
        
        try:
            combustivel = pd.read_sql_query(combustivel_sql, conn, params=(self.veiculo_id,))
            manutencao = pd.read_sql_query(manutencao_sql, conn, params=(self.veiculo_id,))
            conn.close()
            
            return combustivel, manutencao
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return None, None
    
    def treinar(self):
        """Treina modelo com histórico de combustível"""
        combustivel, manutencao = self.carregar_dados()
        
        if combustivel is None or len(combustivel) < 5:
            return {"erro": "Dados insuficientes para treinar modelo", "dados_minimos": 5}
        
        combustivel['data'] = pd.to_datetime(combustivel['data'])
        combustivel['mes'] = combustivel['data'].dt.month
        combustivel['dia_ano'] = combustivel['data'].dt.dayofyear
        
        if len(combustivel) < 10:
            X = combustivel[['quilometragem', 'mes']].values
        else:
            X = combustivel[['quilometragem', 'mes', 'dia_ano']].values
        
        y = combustivel['valor_combustivel'].values
        
        if len(y) < 5:
            return {"erro": "Dados insuficientes"}
        
        try:
            X_scaled = self.scaler.fit_transform(X)
            self.modelo = GradientBoostingRegressor(
                n_estimators=50,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )
            self.modelo.fit(X_scaled, y)
            
            self._salvar_modelo()
            
            return {
                "sucesso": True,
                "registros_usados": len(combustivel),
                "valor_medio": round(float(y.mean()), 2),
                "valor_minimo": round(float(y.min()), 2),
                "valor_maximo": round(float(y.max()), 2)
            }
        except Exception as e:
            return {"erro": str(e)}
    
    def prever_custo_proximo_mes(self, km_estimado=1500):
        """Prevê custo para próximo mês"""
        try:
            if not self._carregar_modelo():
                self.treinar()
            
            if self.modelo is None:
                return {"erro": "Não foi possível treinar o modelo"}
            
            mes_proximo = (datetime.now().month % 12) + 1
            dia_ano = (datetime.now() + timedelta(days=30)).timetuple().tm_yday
            
            X_novo = np.array([[km_estimado, mes_proximo, dia_ano]])
            X_novo_scaled = self.scaler.transform(X_novo)
            
            predicao = self.modelo.predict(X_novo_scaled)[0]
            
            return {
                "sucesso": True,
                "custo_previsto": round(float(max(0, predicao)), 2),
                "km_estimado": km_estimado,
                "mes": mes_proximo,
                "confianca": "Alta" if len(self.carregar_dados()[0]) > 10 else "Média"
            }
        except Exception as e:
            return {"erro": str(e)}
    
    def _salvar_modelo(self):
        """Salva modelo treinado em arquivo"""
        try:
            joblib.dump(self.modelo, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
        except Exception as e:
            print(f"Erro ao salvar modelo: {e}")
    
    def _carregar_modelo(self):
        """Carrega modelo salvo"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.modelo = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                return True
            return False
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            return False


class ModeloRiscoFalha:
    def __init__(self, veiculo_id=None):
        self.veiculo_id = veiculo_id
        self.modelo = None
        self.model_path = f"{MODELS_DIR}/risco_modelo_{veiculo_id}.pkl"
    
    def carregar_dados(self):
        """Carrega dados de checklists"""
        conn = get_conn()
        
        sql = """
            SELECT 
                DATE(c.data) as data,
                CAST(c.quilometragem AS REAL) as quilometragem,
                COUNT(CASE WHEN ci.status='Danificado' THEN 1 END) as danos,
                COUNT(ci.id) as total_itens
            FROM checklist c
            LEFT JOIN checklist_itens ci ON c.id = ci.checklist_id
            WHERE c.veiculo_id = ?
            GROUP BY DATE(c.data)
            ORDER BY c.data ASC
        """
        
        try:
            checklists = pd.read_sql_query(sql, conn, params=(self.veiculo_id,))
            conn.close()
            return checklists
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return None
    
    def treinar(self):
        """Treina modelo para identificar risco de falha"""
        checklists = self.carregar_dados()
        
        if checklists is None or len(checklists) < 5:
            return {"erro": "Dados insuficientes para treinar modelo", "dados_minimos": 5}
        
        checklists['taxa_dano'] = checklists['danos'] / checklists['total_itens'].clip(lower=1)
        checklists['risco_label'] = (checklists['taxa_dano'] > 0.25).astype(int)
        
        if checklists['risco_label'].sum() == 0 or checklists['risco_label'].sum() == len(checklists):
            return {
                "aviso": "Dados desequilibrados, usando modelo linear",
                "registros_usados": len(checklists)
            }
        
        try:
            X = checklists[['quilometragem', 'danos', 'total_itens']].values
            y = checklists['risco_label'].values
            
            self.modelo = RandomForestRegressor(
                n_estimators=50,
                max_depth=5,
                random_state=42,
                min_samples_split=2
            )
            self.modelo.fit(X, y)
            
            self._salvar_modelo()
            
            return {
                "sucesso": True,
                "registros_usados": len(checklists),
                "taxa_risco": round(float(checklists['risco_label'].mean()) * 100, 1),
                "importancia_features": {
                    "quilometragem": round(float(self.modelo.feature_importances_[0]), 3),
                    "danos": round(float(self.modelo.feature_importances_[1]), 3),
                    "total_itens": round(float(self.modelo.feature_importances_[2]), 3)
                }
            }
        except Exception as e:
            return {"erro": str(e)}
    
    def prever_risco(self, km_atual, danos_recentes, total_itens=20):
        """Prevê risco de falha: 0-100%"""
        try:
            if not self._carregar_modelo():
                self.treinar()
            
            if self.modelo is None:
                return {"erro": "Não foi possível treinar o modelo"}
            
            X_novo = np.array([[km_atual, danos_recentes, total_itens]])
            risco_score = self.modelo.predict(X_novo)[0]
            risco_percentual = max(0, min(100, risco_score * 100))
            
            if risco_percentual > 70:
                nivel = "CRÍTICO"
                cor = "danger"
            elif risco_percentual > 50:
                nivel = "ALTO"
                cor = "warning"
            elif risco_percentual > 30:
                nivel = "MÉDIO"
                cor = "info"
            else:
                nivel = "BAIXO"
                cor = "success"
            
            return {
                "sucesso": True,
                "risco": round(risco_percentual, 1),
                "nivel": nivel,
                "cor": cor,
                "recomendacao": self._gerar_recomendacao(nivel, danos_recentes, km_atual)
            }
        except Exception as e:
            return {"erro": str(e)}
    
    def _gerar_recomendacao(self, nivel, danos, km):
        """Gera recomendação baseada no risco"""
        if nivel == "CRÍTICO":
            return "⚠️ Manutenção urgente recomendada. Verifique todos os itens críticos imediatamente."
        elif nivel == "ALTO":
            return "🔧 Agende manutenção em breve. Problemas recorrentes detectados."
        elif nivel == "MÉDIO":
            return "📋 Monitore próximos checklists. Alguns itens requerem atenção."
        else:
            return "✅ Veículo em bom estado. Continue com revisões periódicas."
    
    def _salvar_modelo(self):
        """Salva modelo treinado"""
        try:
            joblib.dump(self.modelo, self.model_path)
        except Exception as e:
            print(f"Erro ao salvar modelo: {e}")
    
    def _carregar_modelo(self):
        """Carrega modelo salvo"""
        try:
            if os.path.exists(self.model_path):
                self.modelo = joblib.load(self.model_path)
                return True
            return False
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}")
            return False


def treinar_todos_modelos():
    """Treina modelos para todos os veículos"""
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT DISTINCT veiculo_id FROM combustivel")
    veiculos = cur.fetchall()
    conn.close()
    
    resultados = {}
    for (veiculo_id,) in veiculos:
        modelo_custo = ModeloPrecaoCustos(veiculo_id)
        modelo_risco = ModeloRiscoFalha(veiculo_id)
        
        resultados[veiculo_id] = {
            "custo": modelo_custo.treinar(),
            "risco": modelo_risco.treinar()
        }
    
    return resultados
