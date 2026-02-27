// Funcionalidade de upload de foto do condutor
document.addEventListener('DOMContentLoaded', function() {
  const photoContainer = document.getElementById('photoPreview');
  const photoInput = document.getElementById('foto_condutor');
  const removePhotoBtn = document.getElementById('removePhoto');

  if (photoContainer && photoInput) {
    // Evento de clique no container para abrir seletor de arquivo
    photoContainer.addEventListener('click', function() {
      photoInput.click();
    });

    // Evento de mudança no input de arquivo
    photoInput.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
          const img = new Image();
          img.onload = function() {
            // Criar canvas para redimensionar para 200x200px
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            // Manter proporção quadrada
            const size = 200;
            canvas.width = size;
            canvas.height = size;

            // Desenhar imagem no canvas
            ctx.drawImage(img, 0, 0, size, size);

            // Converter para blob e mostrar preview
            canvas.toBlob(function(blob) {
              const url = URL.createObjectURL(blob);

              // Remover preview anterior
              const existingPreview = photoContainer.querySelector('.photo-preview');
              if (existingPreview) {
                existingPreview.remove();
              }

              // Criar elemento de preview
              const preview = document.createElement('img');
              preview.src = url;
              preview.className = 'photo-preview show';

              // Ocultar placeholder
              const placeholder = photoContainer.querySelector('.photo-placeholder');
              if (placeholder) {
                placeholder.classList.add('show');
              }

              photoContainer.appendChild(preview);
              removePhotoBtn.style.display = 'inline-block';
            }, 'image/jpeg', 0.85);
          };
          img.src = e.target.result;
        };
        reader.readAsDataURL(file);
      }
    });

    // Evento de clique no botão remover
    if (removePhotoBtn) {
      removePhotoBtn.addEventListener('click', function() {
        photoInput.value = '';
        const preview = photoContainer.querySelector('.photo-preview');
        if (preview) {
          preview.remove();
        }
        const placeholder = photoContainer.querySelector('.photo-placeholder');
        if (placeholder) {
          placeholder.classList.remove('show');
        }
        removePhotoBtn.style.display = 'none';
      });
    }
  }
});
