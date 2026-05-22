from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin
from models import User
from db import get_conn
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import mimetypes
from image_utils import optimize_profile_photo
from config import ANEXOS_DIR

auth_bp = Blueprint('auth', __name__)

UPLOAD_FOLDER = ANEXOS_DIR
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024

def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_safe_redirect_url(target):
    if not target:
        return False

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def get_safe_next_url():
    next_page = request.form.get('next') or request.args.get('next')
    if is_safe_redirect_url(next_page):
        return next_page
    return url_for('dashboard')

def save_profile_photo(file):
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        flash('Tipo de arquivo não permitido. Use JPG, PNG ou GIF.', 'error')
        return None
    
    if len(file.read()) > MAX_FILE_SIZE:
        file.seek(0)
        flash('Arquivo muito grande. Máximo 5MB.', 'error')
        return None
    
    file.seek(0)
    ensure_upload_folder()
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"profile_{current_user.id}_{datetime.now().timestamp()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    return filename

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.find_by_username(username)
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(get_safe_next_url())
        else:
            flash('Usuário ou senha inválidos', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'admin':
        flash('Apenas administradores podem criar novos usuários', 'error')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role', 'usuario')
        
        if User.find_by_username(username):
            flash('Nome de usuário já está em uso', 'error')
        else:
            is_admin = (role == 'admin')
            User.create(username, password, email=email, is_admin=is_admin, role=role)
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('auth.manage_users'))
            
    return render_template('register.html')

@auth_bp.route('/gerenciar-usuarios', methods=['GET'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.get_all_users()
    return render_template('manage_users.html', users=users)

@auth_bp.route('/usuario/<int:user_id>/role', methods=['POST'])
@login_required
def update_user_role(user_id):
    if current_user.role != 'admin':
        flash('Você não tem permissão para fazer isso.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.get(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('auth.manage_users'))
    
    new_role = request.form.get('role', 'usuario')
    # Permitir roles customizados além de admin e usuario
    user.update_role(new_role)
    flash(f'Nível de acesso de {user.username} atualizado para {new_role}!', 'success')
    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        profile_photo = None
        
        if not username:
            flash('Nome de usuário é obrigatório.', 'error')
            return redirect(url_for('auth.edit_profile'))
        
        if username != current_user.username:
            if User.find_by_username(username):
                flash('Nome de usuário já está em uso.', 'error')
                return redirect(url_for('auth.edit_profile'))
        
        if new_password or confirm_password:
            if not current_password:
                flash('Senha atual é obrigatória para alterar a senha.', 'error')
                return redirect(url_for('auth.edit_profile'))
            
            if not current_user.check_password(current_password):
                flash('Senha atual incorreta.', 'error')
                return redirect(url_for('auth.edit_profile'))
            
            if new_password != confirm_password:
                flash('As senhas não conferem.', 'error')
                return redirect(url_for('auth.edit_profile'))
            
            if len(new_password) < 8:
                flash('A nova senha deve ter pelo menos 8 caracteres.', 'error')
                return redirect(url_for('auth.edit_profile'))
            
            current_user.set_password(new_password)
        
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename != '':
                saved_filename = save_profile_photo(file)
                if saved_filename:
                    profile_photo = saved_filename
        
        current_user.update_profile(username=username, email=email, profile_photo=profile_photo)
        
        # Recarregar dados do usuário na sessão
        refreshed_user = User.get(current_user.id)
        if refreshed_user:
            current_user.username = refreshed_user.username
            current_user.email = refreshed_user.email
            current_user.profile_photo = refreshed_user.profile_photo
            current_user.password_hash = refreshed_user.password_hash
        
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_profile.html')

@auth_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Deletar a conta do usuário logado"""
    try:
        user_id = current_user.id
        
        # Deletar a conta do usuário
        User.delete(user_id)
        
        # Fazer logout do usuário
        logout_user()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/usuario/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Editar um usuário (apenas admins)"""
    if current_user.role != 'admin':
        flash('Você não tem permissão para fazer isso.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.get(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('auth.manage_users'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        if not username:
            flash('Nome de usuário é obrigatório.', 'error')
            return redirect(url_for('auth.edit_user', user_id=user_id))
        
        # Verificar se o novo username já existe (exceto para o próprio usuário)
        if username != user.username:
            if User.find_by_username(username):
                flash('Nome de usuário já está em uso.', 'error')
                return redirect(url_for('auth.edit_user', user_id=user_id))
        
        # Atualizar usuário
        user.update_profile(username=username, email=email)
        flash(f'Usuário {username} atualizado com sucesso!', 'success')
        return redirect(url_for('auth.manage_users'))
    
    return render_template('edit_user.html', user=user)

@auth_bp.route('/usuario/<int:user_id>/deletar', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    """Deletar um usuário (apenas admins)"""
    if current_user.role != 'admin':
        flash('Você não tem permissão para fazer isso.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        flash('Use o botão de exclusão na lista de usuários para confirmar a ação.', 'warning')
        return redirect(url_for('auth.manage_users'))

    # Não permitir que um admin delete a si mesmo
    if user_id == current_user.id:
        flash('Você não pode deletar sua própria conta.', 'error')
        return redirect(url_for('auth.manage_users'))
    
    try:
        user = User.get(user_id)
        if not user:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('auth.manage_users'))

        username = user.username
        User.delete(user_id)
        flash(f'Usuário {username} deletado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao deletar usuário: {e}', 'danger')

    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/usuario/<int:user_id>/toggle-active', methods=['POST'])
@login_required
def toggle_user_active(user_id):
    """Ativar/Inativar um usuário (apenas admins)"""
    if current_user.role != 'admin':
        flash('Você não tem permissão para fazer isso.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Não permitir que um admin inative a si mesmo
    if user_id == current_user.id:
        flash('Você não pode inativar sua própria conta.', 'error')
        return redirect(url_for('auth.manage_users'))
    
    user = User.get(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('auth.manage_users'))
    
    user.toggle_active()
    status = "ativado" if user.is_active else "inativado"
    flash(f'Usuário {user.username} {status} com sucesso!', 'success')
    return redirect(url_for('auth.manage_users'))
