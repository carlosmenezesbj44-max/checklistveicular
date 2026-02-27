# Estratégia: Modo Offline com Sincronização

## Visão Geral
Implementar a capacidade de usar a aplicação em áreas sem sinal, armazenando dados localmente no navegador e sincronizando quando a conexão voltar.

## Arquitetura

### 1. **Storage Local (IndexedDB + LocalStorage)**
```
┌─────────────────────────────────────────────────────┐
│         Frontend (Browser)                          │
├─────────────────────────────────────────────────────┤
│ IndexedDB                                           │
│ ├── checklists (offline)                            │
│ ├── combustivel (offline)                           │
│ ├── manutencao (offline)                            │
│ └── sync_queue (operações pendentes)                │
│                                                     │
│ LocalStorage                                        │
│ ├── offline_flag (true/false)                       │
│ ├── last_sync (timestamp)                           │
│ └── user_id                                         │
└─────────────────────────────────────────────────────┘
         ↓ (quando online)
┌─────────────────────────────────────────────────────┐
│         Backend (Flask/Python)                      │
├─────────────────────────────────────────────────────┤
│ API Endpoints                                       │
│ ├── /api/sync (recebe batch de mudanças)           │
│ ├── /api/status (verifica conectividade)           │
│ └── /api/resolve-conflicts (resolve conflitos)     │
│                                                     │
│ Database (SQLite/PostgreSQL)                        │
└─────────────────────────────────────────────────────┘
```

---

## 2. Implementação - Estrutura de Pastas

```
checklist-carros/
├── static/
│   └── js/
│       ├── offline/
│       │   ├── db.js (IndexedDB operations)
│       │   ├── sync-manager.js (sync logic)
│       │   ├── conflict-resolver.js (conflict handling)
│       │   └── queue.js (pending operations)
│       ├── offline-ui.js (UI indicators)
│       └── app-offline.js (initialization)
├── templates/
│   └── base.html (add offline indicator)
└── app.py (add sync endpoints)
```

---

## 3. Componentes Principais

### A. Inicialização do IndexedDB (`static/js/offline/db.js`)

```javascript
class OfflineDatabase {
  constructor() {
    this.dbName = 'ChecklistDB';
    this.version = 1;
    this.db = null;
  }

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Criar object stores
        if (!db.objectStoreNames.contains('checklists')) {
          db.createObjectStore('checklists', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('combustivel')) {
          db.createObjectStore('combustivel', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('manutencao')) {
          db.createObjectStore('manutencao', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('sync_queue')) {
          db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
        }
      };
    });
  }

  async save(storeName, data) {
    const tx = this.db.transaction([storeName], 'readwrite');
    const store = tx.objectStore(storeName);
    return new Promise((resolve, reject) => {
      const request = store.put(data);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async get(storeName, id) {
    const tx = this.db.transaction([storeName], 'readonly');
    const store = tx.objectStore(storeName);
    return new Promise((resolve, reject) => {
      const request = store.get(id);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async getAll(storeName) {
    const tx = this.db.transaction([storeName], 'readonly');
    const store = tx.objectStore(storeName);
    return new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async delete(storeName, id) {
    const tx = this.db.transaction([storeName], 'readwrite');
    const store = tx.objectStore(storeName);
    return new Promise((resolve, reject) => {
      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
}
```

### B. Gerenciador de Sincronização (`static/js/offline/sync-manager.js`)

```javascript
class SyncManager {
  constructor(offlineDb) {
    this.db = offlineDb;
    this.isSyncing = false;
    this.lastSync = localStorage.getItem('last_sync') || null;
  }

  async queueOperation(operation, data) {
    // operation: 'CREATE', 'UPDATE', 'DELETE'
    const queueItem = {
      id: Date.now(),
      type: operation,
      timestamp: new Date().toISOString(),
      collection: data.collection,
      data: data,
      status: 'pending',
      retries: 0
    };

    await this.db.save('sync_queue', queueItem);
    console.log(`[Offline] Operação enfileirada:`, queueItem);
  }

  async sync() {
    if (this.isSyncing || !navigator.onLine) {
      console.log('[Offline] Não é possível sincronizar');
      return false;
    }

    this.isSyncing = true;
    try {
      const pendingOps = await this.db.getAll('sync_queue');
      
      if (pendingOps.length === 0) {
        console.log('[Sync] Nenhuma operação pendente');
        return true;
      }

      // Enviar batch ao servidor
      const response = await fetch('/api/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          operations: pendingOps,
          last_sync: this.lastSync,
          user_id: localStorage.getItem('user_id')
        })
      });

      if (!response.ok) {
        throw new Error(`Sync failed: ${response.statusText}`);
      }

      const result = await response.json();

      // Processar resultado (conflitos, etc)
      if (result.conflicts && result.conflicts.length > 0) {
        await this.handleConflicts(result.conflicts);
      }

      // Limpar sync_queue
      for (const op of pendingOps) {
        await this.db.delete('sync_queue', op.id);
      }

      this.lastSync = new Date().toISOString();
      localStorage.setItem('last_sync', this.lastSync);

      console.log('[Sync] Sincronização concluída com sucesso');
      return true;

    } catch (error) {
      console.error('[Sync] Erro ao sincronizar:', error);
      return false;
    } finally {
      this.isSyncing = false;
    }
  }

  async handleConflicts(conflicts) {
    // Implementar estratégia de resolução de conflitos
    // Opções: last-write-wins, manual resolution, server-wins
    for (const conflict of conflicts) {
      console.warn('[Conflict] Conflito detectado:', conflict);
      // TODO: Notificar usuário e solicitar resolução manual
    }
  }
}
```

### C. Indicador de Status Offline (`static/js/offline/offline-ui.js`)

```javascript
class OfflineUI {
  constructor() {
    this.indicator = null;
    this.syncButton = null;
    this.init();
  }

  init() {
    // Criar indicador visual
    const indicator = document.createElement('div');
    indicator.id = 'offline-indicator';
    indicator.className = 'offline-indicator online';
    indicator.innerHTML = `
      <span class="status-icon">●</span>
      <span class="status-text">Online</span>
      <button id="sync-btn" class="sync-btn">Sincronizar</button>
    `;
    document.body.insertBefore(indicator, document.body.firstChild);

    this.indicator = indicator;
    this.syncButton = indicator.querySelector('#sync-btn');

    window.addEventListener('online', () => this.setOnline());
    window.addEventListener('offline', () => this.setOffline());
  }

  setOnline() {
    this.indicator.classList.remove('offline');
    this.indicator.classList.add('online');
    this.indicator.querySelector('.status-text').textContent = 'Online';
    this.indicator.querySelector('.status-icon').textContent = '●';
  }

  setOffline() {
    this.indicator.classList.remove('online');
    this.indicator.classList.add('offline');
    this.indicator.querySelector('.status-text').textContent = 'Offline';
    this.indicator.querySelector('.status-icon').textContent = '⚠';
  }

  showSyncStatus(status) {
    const statusMap = {
      'syncing': 'Sincronizando...',
      'success': 'Sincronizado',
      'error': 'Erro na sincronização'
    };
    this.indicator.querySelector('.status-text').textContent = statusMap[status];
  }
}
```

### D. CSS para Indicador (`static/css/offline.css`)

```css
.offline-indicator {
  position: fixed;
  top: 0;
  right: 0;
  padding: 10px 15px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  z-index: 10000;
  transition: all 0.3s ease;
}

.offline-indicator.online {
  background-color: #4CAF50;
  color: white;
}

.offline-indicator.offline {
  background-color: #FF9800;
  color: white;
  box-shadow: 0 0 10px rgba(255, 152, 0, 0.5);
}

.status-icon {
  font-weight: bold;
  font-size: 16px;
}

.sync-btn {
  padding: 4px 8px;
  margin-left: 8px;
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.5);
  color: white;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.sync-btn:hover {
  background: rgba(255, 255, 255, 0.5);
}

.offline-indicator.offline .sync-btn {
  display: none;
}
```

---

## 4. Backend - Endpoints de Sincronização

### `app.py` - Adicionar endpoints

```python
from flask import request, jsonify
from datetime import datetime
import json

@app.route('/api/sync', methods=['POST'])
@login_required
def sync_offline_data():
    """Recebe dados offline e sincroniza com o servidor"""
    try:
        data = request.get_json()
        operations = data.get('operations', [])
        user_id = current_user.id
        
        conn = get_conn()
        cur = conn.cursor()
        
        results = {
            'synced': [],
            'conflicts': [],
            'errors': []
        }
        
        for op in operations:
            try:
                if op['type'] == 'CREATE':
                    handle_create(cur, op, user_id)
                elif op['type'] == 'UPDATE':
                    handle_update(cur, op, user_id)
                elif op['type'] == 'DELETE':
                    handle_delete(cur, op, user_id)
                
                results['synced'].append(op['id'])
            except ConflictError as e:
                results['conflicts'].append({
                    'operation_id': op['id'],
                    'reason': str(e),
                    'server_data': e.server_data
                })
            except Exception as e:
                results['errors'].append({
                    'operation_id': op['id'],
                    'error': str(e)
                })
        
        conn.commit()
        conn.close()
        
        return jsonify(results), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def connection_status():
    """Verifica status de conexão"""
    return jsonify({
        'online': True,
        'timestamp': datetime.now().isoformat(),
        'user_id': current_user.id if current_user.is_authenticated else None
    })
```

---

## 5. Integração no Frontend

### Inicializar no template `base.html`

```html
<!DOCTYPE html>
<html>
<head>
    <!-- ... existing head ... -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/offline.css') }}">
</head>
<body>
    <!-- ... existing content ... -->
    
    <script src="{{ url_for('static', filename='js/offline/db.js') }}"></script>
    <script src="{{ url_for('static', filename='js/offline/sync-manager.js') }}"></script>
    <script src="{{ url_for('static', filename='js/offline/offline-ui.js') }}"></script>
    <script>
        // Inicializar sistema offline
        (async () => {
            const offlineDb = new OfflineDatabase();
            await offlineDb.init();
            
            const syncManager = new SyncManager(offlineDb);
            const offlineUI = new OfflineUI();
            
            // Sincronizar a cada 30 segundos se online
            setInterval(async () => {
                if (navigator.onLine) {
                    offlineUI.showSyncStatus('syncing');
                    const success = await syncManager.sync();
                    offlineUI.showSyncStatus(success ? 'success' : 'error');
                }
            }, 30000);
            
            // Botão manual de sincronização
            document.getElementById('sync-btn').addEventListener('click', async () => {
                await syncManager.sync();
            });
            
            // Expor globalmente para uso em páginas
            window.offlineDb = offlineDb;
            window.syncManager = syncManager;
        })();
    </script>
</body>
</html>
```

---

## 6. Exemplo: Salvar Checklist Offline

```javascript
// No formulário de checklist
async function salvarChecklistOffline(formData) {
    if (!navigator.onLine) {
        // Modo offline - salvar no IndexedDB
        await window.offlineDb.save('checklists', {
            id: Date.now(),
            ...formData,
            _offline: true,
            _timestamp: new Date().toISOString()
        });
        
        // Enfileirar para sincronização
        await window.syncManager.queueOperation('CREATE', {
            collection: 'checklists',
            data: formData
        });
        
        alert('Checklist salvo localmente. Será sincronizado quando voltar online.');
    } else {
        // Modo online - enviar normalmente
        const response = await fetch('/salvar-checklist', {
            method: 'POST',
            body: new FormData(document.querySelector('form'))
        });
        return response;
    }
}
```

---

## 7. Estratégia de Conflitos

### Tipos de Conflitos:
1. **Last-Write-Wins**: Usar timestamp para determinar versão mais recente
2. **Server-Wins**: Sempre usar dados do servidor
3. **Manual Resolution**: Notificar usuário e solicitar escolha

### Exemplo de Resolução:

```javascript
async function resolveConflict(localData, serverData) {
    // Comparar timestamps
    const localTime = new Date(localData._timestamp).getTime();
    const serverTime = new Date(serverData.updated_at).getTime();
    
    if (localTime > serverTime) {
        // Local é mais recente, usar local
        return localData;
    } else {
        // Server é mais recente, usar server
        return serverData;
    }
}
```

---

## 8. Testes

```bash
# Teste 1: Modo offline
- Desabilitar conexão no DevTools
- Preencher formulário
- Verificar armazenamento em IndexedDB
- Reabilitar conexão
- Verificar sincronização automática

# Teste 2: Conflitos
- Modificar dados offline
- Modificar mesmo dado no servidor
- Reabilitar conexão
- Verificar resolução de conflito

# Teste 3: Performance
- Enviar múltiplas operações offline
- Medir tempo de sincronização
- Verificar sem falhas
```

---

## 9. Próximos Passos

- [ ] Implementar IndexedDB e sync manager
- [ ] Adicionar endpoints de sync no backend
- [ ] Criar UI de status offline
- [ ] Implementar resolução de conflitos
- [ ] Testes de sincronização
- [ ] Documentação de uso para usuários
- [ ] Performance monitoring
- [ ] Suporte a imagens offline (cache storage)

