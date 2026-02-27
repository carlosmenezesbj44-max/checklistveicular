// Funcionalidade de upload de foto
document.addEventListener('DOMContentLoaded', function() {
  const photoContainer = document.getElementById('photoPreview');
  const photoInput = document.getElementById('profile_photo');
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
            // Criar canvas para redimensionar para 3x4 (150x200px)
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            // Calcular proporção 3:4
            let width = 150;
            let height = 200;

            const aspectRatio = img.width / img.height;
            if (aspectRatio > 0.75) {
              // Imagem mais larga que 3:4, ajustar largura
              width = 150;
              height = width / aspectRatio;
            } else {
              // Imagem mais alta que 3:4, ajustar altura
              height = 200;
              width = height * aspectRatio;
            }

            canvas.width = width;
            canvas.height = height;

            // Desenhar imagem no canvas
            ctx.drawImage(img, 0, 0, width, height);

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
              if (removePhotoBtn) {
                removePhotoBtn.style.display = 'inline-block';
              }
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
