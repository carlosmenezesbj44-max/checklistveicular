# Guia de Dark Mode

## ✅ O que foi implementado

Um sistema completo de Dark Mode foi adicionado ao aplicativo com suporte total para todos os componentes:

### 🎨 Componentes Estilizados

- **Navbar**: Gradiente escuro com contraste adequado
- **Cards**: Fundo escuro com bordas visíveis
- **Tabelas**: Cores de texto e fundo otimizadas
- **Modais**: Design escuro consistente
- **Botões**: Estilos ajustados para dark mode
- **Inputs/Forms**: Campos com fundo escuro e texto legível
- **Badges**: Cores vibrantes em fundo escuro
- **Dropdowns**: Menu com tema escuro
- **Alertas**: Alertas de sucesso, erro, aviso e info em dark mode
- **Scrollbar**: Scroll bar estilizado
- **Tooltips/Popovers**: Visuais ajustados
- **Breadcrumb**: Navegação com tema escuro
- **Progress bars**: Indicadores com cores apropriadas

### 🎛️ Botão de Alternância

- Localização: Canto superior direito da navbar (ao lado do menu do usuário)
- Ícone: Lua (🌙) para ativar dark mode / Sol (☀️) para ativar light mode
- Comportamento: Transição suave entre temas
- Persistência: A preferência é salva em localStorage

### 💾 Armazenamento de Preferência

A escolha do usuário é salva automaticamente em `localStorage` com a chave `darkMode`:
- `true` = Dark Mode ativado
- `false` = Light Mode ativado
- `null/undefined` = Usa a preferência do sistema (via `prefers-color-scheme`)

### 🎯 Cores Utilizadas

#### Dark Mode
- **Background**: `#0f172a` a `#1e293b` (gradiente)
- **Text Principal**: `#e2e8f0` (branco claro)
- **Text Secundário**: `#cbd5e1` (cinza claro)
- **Text Muted**: `#94a3b8` (cinza mais escuro)
- **Primary Color**: `#10b981` (verde mantido)
- **Borders**: `#334155` (cinza escuro)

#### Light Mode (Original)
- **Background**: `#f8fafc` a `#e2e8f0` (gradiente)
- **Text**: `#1f2937` (preto/cinza escuro)
- **Borders**: `#e2e8f0` (cinza claro)

## 🚀 Como Usar

### Para os Usuários

1. Clique no botão de tema no canto superior direito da navbar (🌙/☀️)
2. O tema mudará instantaneamente
3. Sua preferência será salva e mantida entre sessões

### Para Desenvolvedores

Todos os estilos de dark mode estão definidos em `static/css/styles.css` seguindo o padrão:

```css
body.dark-mode .elemento {
  /* Estilos para dark mode */
}
```

Para adicionar novos estilos de dark mode para um novo componente:

```css
body.dark-mode .meu-componente {
  background-color: #1e293b;  /* Fundo escuro */
  color: #cbd5e1;              /* Texto claro */
  border-color: #334155;       /* Bordas escuras */
}
```

## 📋 Checklist de Componentes

### Navbar ✅
- [x] Fundo com gradiente escuro
- [x] Links com cor clara
- [x] Dropdown menu estilizado
- [x] Brand logo legível

### Content Area ✅
- [x] Cards com fundo escuro
- [x] Headers com gradient
- [x] Títulos em cor clara
- [x] Texto do corpo em cinza claro

### Forms & Inputs ✅
- [x] Input fields com fundo escuro
- [x] Labels em cor clara
- [x] Placeholders legíveis
- [x] Focus states visíveis
- [x] Select dropdowns

### Tables ✅
- [x] Headers com fundo escuro
- [x] Body com cores alternadas
- [x] Hover states
- [x] Textos legíveis

### Modals ✅
- [x] Content com fundo escuro
- [x] Headers com gradient
- [x] Body com texto claro
- [x] Close button visível

### Buttons ✅
- [x] Primary buttons
- [x] Secondary buttons
- [x] Outline buttons
- [x] Danger buttons

### Alerts ✅
- [x] Alert Success
- [x] Alert Danger
- [x] Alert Warning
- [x] Alert Info

### Lists ✅
- [x] List items
- [x] List group items
- [x] Hover states
- [x] Active states

### Misc ✅
- [x] Scrollbar
- [x] Breadcrumb
- [x] Badges
- [x] Progress bars
- [x] Pagination
- [x] Tooltips
- [x] Popovers
- [x] Code blocks
- [x] Spinners

## 🔧 Arquivos Modificados

1. **static/css/styles.css**
   - Adicionadas mais de 250 linhas de estilos de dark mode
   - Classes `.dark-mode` para todos os componentes

2. **templates/base.html**
   - Adicionado botão de alternância de tema
   - Adicionado script de controle de tema
   - Suporte a `localStorage` para persistência

## 🎬 Transições Suaves

Todas as mudanças de tema possuem transições suaves de 0.3 segundos:

```css
body {
  transition: background-color 0.3s ease, color 0.3s ease;
}
```

## 📱 Responsividade

O dark mode funciona perfeitamente em:
- ✅ Desktop
- ✅ Tablet
- ✅ Mobile

## 🌐 Compatibilidade

Testado em:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

## 💡 Dicas

### Para Melhor Experiência

1. Use o dark mode em ambientes com pouca luz
2. O light mode é melhor para ambientes bem iluminados
3. A preferência do sistema é respeitada se nunca tiver sido alterada

### Performance

- Nenhum impacto significativo de performance
- CSS é compilado eficientemente
- Sem uso de JavaScript pesado

## 🐛 Troubleshooting

### O tema não está sendo aplicado

1. Limpe o cache do navegador (Ctrl+Shift+Del)
2. Verifique se cookies/localStorage estão ativados
3. Recarregue a página

### Alguns elementos ainda parecem claros

Se encontrar elementos que não estão estilizados corretamente em dark mode:

1. Verificar se a classe `.dark-mode` está sendo aplicada ao `<body>`
2. Adicionar estilos específicos em `static/css/styles.css`
3. Verificar se não há estilos inline `style="color: ..."`

## 📚 Referências

- Cores base: Tailwind Color Palette
- Padrão de implementação: CSS Custom Properties
- Persistência: LocalStorage API

---

**Versão**: 1.0  
**Data**: 2025-12-24  
**Autor**: Sistema de Dark Mode
