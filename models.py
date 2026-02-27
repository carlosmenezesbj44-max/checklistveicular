from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_conn

class User(UserMixin):
    def __init__(self, id, username, password_hash, email=None, is_admin=False, is_active=True, reset_token=None, reset_token_expiration=None, role=None, profile_photo=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.is_admin = is_admin
        self._is_active = is_active
        self.role = role or ('admin' if is_admin else 'usuario')
        self.reset_token = reset_token
        self.reset_token_expiration = reset_token_expiration
        self.profile_photo = profile_photo

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    @staticmethod
    def get(user_id):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, password_hash, email, is_admin, 
                   reset_token, reset_token_expiration, role, profile_photo, is_active 
            FROM users WHERE id = ?
        """, (user_id,))
        user_data = cur.fetchone()
        if not user_data:
            return None
        return User(
            id=user_data[0],
            username=user_data[1],
            password_hash=user_data[2],
            email=user_data[3],
            is_admin=bool(user_data[4]),
            reset_token=user_data[5],
            reset_token_expiration=user_data[6],
            role=user_data[7],
            profile_photo=user_data[8],
            is_active=bool(user_data[9])
        )

    @staticmethod
    def find_by_username(username):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, password_hash, email, is_admin, 
                   reset_token, reset_token_expiration, role, profile_photo, is_active 
            FROM users WHERE username = ?
        """, (username,))
        user_data = cur.fetchone()
        if not user_data:
            return None
        return User(
            id=user_data[0],
            username=user_data[1],
            password_hash=user_data[2],
            email=user_data[3],
            is_admin=bool(user_data[4]),
            reset_token=user_data[5],
            reset_token_expiration=user_data[6],
            role=user_data[7],
            profile_photo=user_data[8],
            is_active=bool(user_data[9])
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create(username, password, email=None, is_admin=False, role=None, profile_photo=None):
        conn = get_conn()
        cur = conn.cursor()
        password_hash = generate_password_hash(password)
        if role is None:
            role = 'admin' if is_admin else 'usuario'
        cur.execute(
            """
            INSERT INTO users (username, password_hash, email, is_admin, role, profile_photo) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, password_hash, email, 1 if is_admin else 0, role, profile_photo)
        )
        conn.commit()
        return User(cur.lastrowid, username, password_hash, email, is_admin, role=role, profile_photo=profile_photo)
        
    def update_profile(self, username=None, email=None, new_password=None, profile_photo=None):
        conn = get_conn()
        cur = conn.cursor()
        
        if new_password:
            self.password_hash = generate_password_hash(new_password)
            
        if username:
            self.username = username
            
        if email is not None:
            self.email = email
        
        if profile_photo is not None:
            self.profile_photo = profile_photo
            
        cur.execute("""
            UPDATE users 
            SET username = ?, password_hash = ?, email = ?, profile_photo = ?
            WHERE id = ?
        """, (self.username, self.password_hash, self.email, self.profile_photo, self.id))
        
        conn.commit()
        return True
        
    def set_reset_token(self, token, expiration):
        conn = get_conn()
        cur = conn.cursor()
        self.reset_token = token
        self.reset_token_expiration = expiration
        
        cur.execute("""
            UPDATE users 
            SET reset_token = ?, reset_token_expiration = ?
            WHERE id = ?
        """, (token, expiration, self.id))
        
        conn.commit()
        
    @staticmethod
    def verify_reset_token(token):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, password_hash, email, is_admin,
                   reset_token, reset_token_expiration, role, profile_photo 
            FROM users 
            WHERE reset_token = ? AND reset_token_expiration > datetime('now')
        """, (token,))
        
        user_data = cur.fetchone()
        if not user_data:
            return None
            
        return User(
            id=user_data[0],
            username=user_data[1],
            password_hash=user_data[2],
            email=user_data[3],
            is_admin=bool(user_data[4]),
            reset_token=user_data[5],
            reset_token_expiration=user_data[6],
            role=user_data[7],
            profile_photo=user_data[8]
        )
        
    def set_password(self, new_password):
        self.password_hash = generate_password_hash(new_password)
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE users 
            SET password_hash = ?, reset_token = NULL, reset_token_expiration = NULL
            WHERE id = ?
        """, (self.password_hash, self.id))
        
        conn.commit()
        return True
    
    def update_role(self, new_role):
        self.role = new_role
        self.is_admin = (new_role == 'admin')
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE users 
            SET role = ?, is_admin = ?
            WHERE id = ?
        """, (self.role, 1 if self.is_admin else 0, self.id))
        
        conn.commit()
        return True
    
    @staticmethod
    def get_all_users():
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, password_hash, email, is_admin, 
                   reset_token, reset_token_expiration, role, profile_photo, is_active 
            FROM users
            ORDER BY username
        """)
        
        rows = cur.fetchall()
        users = []
        for row in rows:
            users.append(User(
                id=row[0],
                username=row[1],
                password_hash=row[2],
                email=row[3],
                is_admin=bool(row[4]),
                reset_token=row[5],
                reset_token_expiration=row[6],
                role=row[7],
                profile_photo=row[8],
                is_active=bool(row[9])
            ))
        
        return users
    
    def toggle_active(self):
        self.is_active = not self.is_active
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE users 
            SET is_active = ?
            WHERE id = ?
        """, (1 if self.is_active else 0, self.id))
        
        conn.commit()
        return True
    
    @staticmethod
    def delete(user_id):
        """Deletar um usuário pelo ID"""
        conn = get_conn()
        cur = conn.cursor()
        
        # Deletar o usuário
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        return True


class Manutencao:
    def __init__(self, id, veiculo_id, nome_peca, data_manutencao, quilometragem_atual, 
                 vida_util_km=None, proxima_manutencao_km=None, valor_peca=None, 
                 mao_de_obra=None, observacoes=None, created_at=None, status='pendente', data_conclusao=None):
        self.id = id
        self.veiculo_id = veiculo_id
        self.nome_peca = nome_peca
        self.data_manutencao = data_manutencao
        self.quilometragem_atual = quilometragem_atual
        self.vida_util_km = vida_util_km
        self.proxima_manutencao_km = proxima_manutencao_km
        self.valor_peca = valor_peca
        self.mao_de_obra = mao_de_obra
        self.observacoes = observacoes
        self.created_at = created_at
        self.status = status
        self.data_conclusao = data_conclusao

    @staticmethod
    def create(veiculo_id, nome_peca, data_manutencao, quilometragem_atual, 
               vida_util_km=None, proxima_manutencao_km=None, valor_peca=None, 
               mao_de_obra=None, observacoes=None):
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO manutencao 
            (veiculo_id, nome_peca, data_manutencao, quilometragem_atual, 
             vida_util_km, proxima_manutencao_km, valor_peca, mao_de_obra, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (veiculo_id, nome_peca, data_manutencao, quilometragem_atual, 
              vida_util_km, proxima_manutencao_km, valor_peca, mao_de_obra, observacoes))
        
        conn.commit()
        return Manutencao(cur.lastrowid, veiculo_id, nome_peca, data_manutencao, 
                         quilometragem_atual, vida_util_km, proxima_manutencao_km, 
                         valor_peca, mao_de_obra, observacoes)

    @staticmethod
    def get_by_veiculo(veiculo_id):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, veiculo_id, nome_peca, data_manutencao, quilometragem_atual,
                   vida_util_km, proxima_manutencao_km, valor_peca, mao_de_obra, 
                   observacoes, created_at, status, data_conclusao
            FROM manutencao 
            WHERE veiculo_id = ?
            ORDER BY data_manutencao DESC
        """, (veiculo_id,))
        
        rows = cur.fetchall()
        manutencoes = []
        for row in rows:
            manutencoes.append(Manutencao(*row))
        
        return manutencoes

    @staticmethod
    def get_by_id(manutencao_id):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, veiculo_id, nome_peca, data_manutencao, quilometragem_atual,
                   vida_util_km, proxima_manutencao_km, valor_peca, mao_de_obra, 
                   observacoes, created_at, status, data_conclusao
            FROM manutencao 
            WHERE id = ?
        """, (manutencao_id,))
        
        row = cur.fetchone()
        if row:
            return Manutencao(*row)
        return None

    def update(self):
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE manutencao 
            SET nome_peca = ?, data_manutencao = ?, quilometragem_atual = ?,
                vida_util_km = ?, proxima_manutencao_km = ?, valor_peca = ?,
                mao_de_obra = ?, observacoes = ?
            WHERE id = ?
        """, (self.nome_peca, self.data_manutencao, self.quilometragem_atual,
              self.vida_util_km, self.proxima_manutencao_km, self.valor_peca,
              self.mao_de_obra, self.observacoes, self.id))
        
        conn.commit()
        return True

    def delete(self):
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM manutencao WHERE id = ?", (self.id,))
        conn.commit()
        return True

    def concluir(self):
        """Marca a manutenção como concluída"""
        from datetime import datetime
        conn = get_conn()
        cur = conn.cursor()
        
        data_conclusao = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        cur.execute("""
            UPDATE manutencao 
            SET status = 'concluida', data_conclusao = ?
            WHERE id = ?
        """, (data_conclusao, self.id))
        
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_all():
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, m.veiculo_id, m.nome_peca, m.data_manutencao, m.quilometragem_atual,
                   m.vida_util_km, m.proxima_manutencao_km, m.valor_peca, m.mao_de_obra, 
                   m.observacoes, m.created_at, COALESCE(m.status, 'pendente'), COALESCE(m.data_conclusao, ''), v.placa, v.modelo, v.condutor
            FROM manutencao m
            JOIN veiculos v ON m.veiculo_id = v.id
            ORDER BY m.data_manutencao DESC
        """)
        
        rows = cur.fetchall()
        manutencoes = []
        for row in rows:
            manutencao = Manutencao(row[0], row[1], row[2], row[3], row[4], 
                                   row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12] if row[12] else None)
            manutencao.veiculo_placa = row[13]
            manutencao.veiculo_modelo = row[14]
            manutencao.veiculo_condutor = row[15]
            manutencoes.append(manutencao)
        
        return manutencoes

    @property
    def custo_total(self):
        if self.valor_peca and self.mao_de_obra:
            return self.valor_peca + self.mao_de_obra
        elif self.valor_peca:
            return self.valor_peca
        elif self.mao_de_obra:
            return self.mao_de_obra
        return 0.0
