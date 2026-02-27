// Script para captura de câmera e OCR de cupons de combustível

async function abrirCameraCombustivel() {
  const modalHtml = `
    <div class="modal fade" id="ocrCameraModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Ler Cupom de Combustível</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div id="ocrStepCamera" style="display: block;">
              <div class="text-center mb-3">
                <p class="text-muted">Aponte para o cupom/nota fiscal do combustível</p>
              </div>
              <video id="ocrVideo" width="100%" height="400" style="border-radius: 8px; background: #000; margin-bottom: 10px;"></video>
              <div class="d-grid gap-2">
                <button class="btn btn-primary btn-lg" id="ocrCapturaBtn">
                  <i class="bi bi-camera"></i> Capturar Foto
                </button>
                <button class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancelar</button>
              </div>
            </div>
            
            <div id="ocrStepProcessando" style="display: none;">
              <div class="text-center">
                <div class="spinner-border text-primary mb-3" role="status">
                  <span class="visually-hidden">Processando...</span>
                </div>
                <p class="text-muted">Analisando cupom... Isso pode levar alguns segundos</p>
              </div>
            </div>
            
            <div id="ocrStepResultado" style="display: none;">
              <div id="ocrResultadoConteudo"></div>
              <div class="d-grid gap-2 mt-3">
                <button class="btn btn-success btn-lg" id="ocrConfirmarBtn">
                  <i class="bi bi-check-circle"></i> Usar Estes Dados
                </button>
                <button class="btn btn-outline-secondary" id="ocrNovaFotoBtn">
                  <i class="bi bi-camera-reels"></i> Capturar Novamente
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Adicionar modal ao DOM se não existir
  if (!document.getElementById('ocrCameraModal')) {
    const modalDiv = document.createElement('div');
    modalDiv.innerHTML = modalHtml;
    document.body.appendChild(modalDiv);
  }
  
  // Mostrar modal
  const modal = new bootstrap.Modal(document.getElementById('ocrCameraModal'));
  modal.show();
  
  // Iniciar câmera
  iniciarCameraCombustivel();
}

async function iniciarCameraCombustivel() {
  const video = document.getElementById('ocrVideo');
  
  // Verificar suporte a getUserMedia
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    console.warn('getUserMedia não disponível, tentando html5-qrcode');
    tentarCameraComHtml5QRCode();
    return;
  }
  
  try {
    // Tentar com câmera traseira (environment) primeiro
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      video.srcObject = stream;
      video.play();
      console.log('Câmera traseira iniciada com sucesso');
      return;
    } catch (error) {
      // Se falhar, tentar sem especificar câmera
      console.warn('Câmera traseira indisponível, tentando câmera padrão');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true
      });
      video.srcObject = stream;
      video.play();
      console.log('Câmera padrão iniciada com sucesso');
    }
  } catch (error) {
    console.error('Erro ao acessar câmera:', error);
    
    // Tentar com html5-qrcode como fallback
    console.log('Tentando fallback com html5-qrcode...');
    tentarCameraComHtml5QRCode();
  }
}

function tentarCameraComHtml5QRCode() {
  // Verificar se html5QrcodeScanner está disponível
  if (typeof Html5QrcodeScanner === 'undefined') {
    mostrarErroCamera('Seu navegador não suporta acesso à câmera. Use Chrome, Firefox, Safari ou Edge.');
    return;
  }
  
  try {
    const video = document.getElementById('ocrVideo');
    const videoParent = video.parentElement;
    
    // Criar container para html5-qrcode
    const qrCodeContainer = document.createElement('div');
    qrCodeContainer.id = 'qr-reader';
    qrCodeContainer.style.width = '100%';
    qrCodeContainer.style.height = '400px';
    qrCodeContainer.style.borderRadius = '8px';
    qrCodeContainer.style.marginBottom = '10px';
    
    // Remover video antigo
    video.style.display = 'none';
    videoParent.insertBefore(qrCodeContainer, video);
    
    // Inicializar scanner
    const scanner = new Html5QrcodeScanner('qr-reader', {
      fps: 10,
      qrbox: 250,
      videoConstraints: { facingMode: 'environment' }
    });
    
    scanner.render(onScanSuccess, onScanError);
    window.qrCodeScanner = scanner; // Guardar referência global
    
    console.log('html5-qrcode iniciado com sucesso');
  } catch (error) {
    console.error('Erro ao iniciar html5-qrcode:', error);
    mostrarErroCamera('Não foi possível inicializar a câmera. ' + error.message);
  }
}

function onScanSuccess(decodedText, decodedResult) {
  console.log('QR Code lido:', decodedText);
  
  // Parar scanner
  if (window.qrCodeScanner) {
    window.qrCodeScanner.clear();
  }
  
  // Mostrar resultado
  document.getElementById('ocrStepCamera').style.display = 'none';
  document.getElementById('ocrStepProcessando').style.display = 'none';
  document.getElementById('ocrStepResultado').style.display = 'block';
  
  const dados = extrairDadosQRCode(decodedText);
  
  let conteudo = `
    <div class="alert alert-success mb-3">
      <i class="bi bi-qr-code"></i> <strong>QR Code lido com sucesso!</strong>
    </div>
    <div class="card bg-light">
      <div class="card-body">
        <h6 class="card-title">Conteúdo do QR Code:</h6>
        <p class="text-monospace small" style="word-break: break-all; background: white; padding: 10px; border-radius: 4px;">
          ${decodedText}
        </p>
        <hr>
        <h6 class="card-title">Dados Extraídos:</h6>
        <table class="table table-sm">
          <tbody>
  `;
  
  if (dados.quantidade_litros) {
    conteudo += `<tr><td class="fw-bold">Litros:</td><td class="text-success">${dados.quantidade_litros.toFixed(2)} L</td></tr>`;
  } else {
    conteudo += `<tr><td class="fw-bold">Litros:</td><td class="text-warning">Não detectado</td></tr>`;
  }
  
  if (dados.valor_total) {
    conteudo += `<tr><td class="fw-bold">Valor:</td><td class="text-success">R$ ${dados.valor_total.toFixed(2)}</td></tr>`;
  } else {
    conteudo += `<tr><td class="fw-bold">Valor:</td><td class="text-warning">Não detectado</td></tr>`;
  }
  
  if (dados.data) {
    conteudo += `<tr><td class="fw-bold">Data:</td><td class="text-success">${new Date(dados.data).toLocaleDateString('pt-BR')}</td></tr>`;
  }
  
  conteudo += `
          </tbody>
        </table>
      </div>
    </div>
    <div class="d-grid gap-2 mt-3">
      <button class="btn btn-success btn-lg" id="qrCodeConfirmarBtn">
        <i class="bi bi-check-circle"></i> Usar Estes Dados
      </button>
      <button class="btn btn-outline-secondary" data-bs-dismiss="modal">Fechar</button>
    </div>
  `;
  
  document.getElementById('ocrResultadoConteudo').innerHTML = conteudo;
  window.ocrDadosExtraidos = dados;
  
  // Adicionar listener ao botão confirmar
  document.getElementById('qrCodeConfirmarBtn').addEventListener('click', confirmarDadosOCR);
}

function onScanError(error) {
  // Ignorar erros de scanning contínuo
  console.debug('Scan error:', error);
}

function mostrarErroCamera(mensagem) {
  // Ocultar modal de câmera
  document.getElementById('ocrStepCamera').style.display = 'none';
  document.getElementById('ocrStepProcessando').style.display = 'none';
  document.getElementById('ocrStepResultado').style.display = 'block';
  
  // Mostrar erro com opções
  document.getElementById('ocrResultadoConteudo').innerHTML = `
    <div class="alert alert-danger" role="alert">
      <h5><i class="bi bi-exclamation-triangle"></i> Erro ao acessar a câmera</h5>
      <p>${mensagem}</p>
      <hr>
      <h6>Soluções:</h6>
      <ul class="mb-0">
        <li>Verifique se o navegador tem permissão para acessar a câmera</li>
        <li>Tente em outro navegador (Chrome, Firefox, Safari)</li>
        <li>Se está em localhost, certifique-se que é http://localhost</li>
        <li>Se em produção, certifique-se que está em HTTPS</li>
        <li>Feche outros aplicativos que possam estar usando a câmera</li>
        <li>Use upload de arquivo como alternativa (abaixo no formulário)</li>
      </ul>
    </div>
    <div class="d-grid gap-2 mt-3">
      <button class="btn btn-outline-secondary" data-bs-dismiss="modal">Fechar</button>
    </div>
  `;
}

function pararCameraCombustivel() {
  const video = document.getElementById('ocrVideo');
  if (video && video.srcObject) {
    video.srcObject.getTracks().forEach(track => track.stop());
  }
}

async function capturarFotoCombustivel() {
  const video = document.getElementById('ocrVideo');
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0);
  
  // Mostrar processando
  document.getElementById('ocrStepCamera').style.display = 'none';
  document.getElementById('ocrStepProcessando').style.display = 'block';
  
  // Usar Tesseract para OCR
  await processarOCRCombustivel(canvas.toDataURL('image/jpeg'));
}

async function processarOCRCombustivel(imagemBase64) {
  try {
    document.getElementById('ocrStepProcessando').style.display = 'block';
    
    // Primeiro, tentar ler QR code
    const qrResult = await lerQRCode(imagemBase64);
    
    if (qrResult && qrResult.data) {
      console.log('QR Code detectado:', qrResult.data);
      // Se QR code foi lido, usar seus dados
      const dados = extrairDadosQRCode(qrResult.data);
      exibirResultadoOCR(dados, imagemBase64, qrResult.data);
      return;
    }
    
    // Se não encontrou QR code, usar OCR tradicional
    console.log('QR Code não encontrado, usando OCR');
    
    // Verificar se Tesseract está disponível
    if (!window.Tesseract) {
      throw new Error('Tesseract.js não está carregado');
    }
    
    const { createWorker } = Tesseract;
    const worker = await createWorker('por');
    
    const result = await worker.recognize(imagemBase64);
    const texto = result.data.text;
    
    await worker.terminate();
    
    // Se conseguiu extrair texto
    if (texto && texto.trim().length > 0) {
      const dados = extrairDadosCombustivel(texto);
      exibirResultadoOCR(dados, imagemBase64);
    } else {
      throw new Error('Nenhum texto foi detectado na imagem');
    }
  } catch (error) {
    console.error('Erro no processamento:', error);
    document.getElementById('ocrStepProcessando').style.display = 'none';
    document.getElementById('ocrStepResultado').style.display = 'block';
    
    let mensagemErro = 'Erro ao processar imagem';
    
    if (error.message.includes('Tesseract')) {
      mensagemErro = 'Erro ao carregar OCR. Tente usar a galeria.';
    } else if (error.message.includes('Nenhum texto')) {
      mensagemErro = 'Nenhum texto ou QR code foi detectado na imagem. Tente outra foto.';
    } else {
      mensagemErro = error.message || mensagemErro;
    }
    
    document.getElementById('ocrResultadoConteudo').innerHTML = `
      <div class="alert alert-danger">
        <i class="bi bi-exclamation-circle"></i> ${mensagemErro}
      </div>
      <div class="alert alert-info">
        <strong>Alternativas:</strong>
        <ul class="mb-0 mt-2">
          <li>Tente capturar a imagem novamente com melhor luz</li>
          <li>Use o upload de arquivo ao invés de câmera</li>
          <li>Preencha os dados manualmente no formulário</li>
        </ul>
      </div>
      <div class="d-grid gap-2 mt-3">
        <button class="btn btn-outline-secondary" data-bs-dismiss="modal">Fechar</button>
      </div>
    `;
  }
}

async function lerQRCode(imagemBase64) {
  return new Promise((resolve) => {
    // Criar imagem a partir do base64
    const img = new Image();
    img.onload = function() {
      try {
        // Criar canvas e desenhar imagem
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        
        // Obter dados da imagem
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        // Usar jsQR para decodificar
        if (window.jsQR) {
          const code = jsQR(imageData.data, imageData.width, imageData.height);
          resolve(code);
        } else {
          console.warn('jsQR não está carregado');
          resolve(null);
        }
      } catch (error) {
        console.error('Erro ao ler QR code:', error);
        resolve(null);
      }
    };
    img.onerror = function() {
      console.error('Erro ao carregar imagem para QR code');
      resolve(null);
    };
    img.src = imagemBase64;
  });
}

function extrairDadosQRCode(qrcodeData) {
  const dados = {
    quantidade_litros: null,
    valor_total: null,
    data: null,
    texto_bruto: qrcodeData,
    origem: 'QR_CODE'
  };
  
  // O QR code pode conter dados estruturados (NFe, MDFe, etc)
  // Tenta extrair valores comuns
  
  // Extrair litros
  const litrosMatch = qrcodeData.match(/(\d+[.,]\d+)\s*[lL]|litros[:\s]+(\d+[.,]\d+)/i);
  if (litrosMatch) {
    const valor = (litrosMatch[1] || litrosMatch[2]).replace(',', '.');
    dados.quantidade_litros = parseFloat(valor);
  }
  
  // Extrair valor
  const valorMatch = qrcodeData.match(/R\$\s*(\d+[.,]\d+)|valor[:\s]+(\d+[.,]\d+)|(\d+[.,]\d{2})/i);
  if (valorMatch) {
    const valor = (valorMatch[1] || valorMatch[2] || valorMatch[3]).replace(',', '.');
    dados.valor_total = parseFloat(valor);
  }
  
  // Extrair data
  const dataMatch = qrcodeData.match(/(\d{2})[/\-](\d{2})[/\-](\d{4})|(\d{4})[/\-](\d{2})[/\-](\d{2})/);
  if (dataMatch) {
    if (dataMatch[3]) {
      dados.data = `${dataMatch[3]}-${dataMatch[2]}-${dataMatch[1]}`;
    } else if (dataMatch[4]) {
      dados.data = `${dataMatch[4]}-${dataMatch[5]}-${dataMatch[6]}`;
    }
  }
  
  return dados;
}

function extrairDadosCombustivel(texto) {
  const dados = {
    quantidade_litros: null,
    valor_total: null,
    data: null,
    texto_bruto: texto
  };
  
  // Extrair litros (padrões comuns: "45,5 L", "45.5L", "LITROS 45.5")
  const litrosMatch = texto.match(/(\d+[.,]\d+)\s*[lL]|LITROS\s+(\d+[.,]\d+)/i);
  if (litrosMatch) {
    const valor = (litrosMatch[1] || litrosMatch[2]).replace(',', '.');
    dados.quantidade_litros = parseFloat(valor);
  }
  
  // Extrair valor total (padrões: "R$ 250,50", "250.50", "TOTAL 250,50")
  const valorMatch = texto.match(/R\$\s*(\d+[.,]\d+)|TOTAL\s*(\d+[.,]\d+)|(\d+[.,]\d{2})(?:\s|$)/i);
  if (valorMatch) {
    const valor = (valorMatch[1] || valorMatch[2] || valorMatch[3]).replace(',', '.');
    dados.valor_total = parseFloat(valor);
  }
  
  // Extrair data (padrões: "01/12/2024", "2024-12-01", "01-12-2024")
  const dataMatch = texto.match(/(\d{2})[/\-](\d{2})[/\-](\d{4})|(\d{4})[/\-](\d{2})[/\-](\d{2})/);
  if (dataMatch) {
    if (dataMatch[3]) {
      // DD/MM/YYYY
      dados.data = `${dataMatch[3]}-${dataMatch[2]}-${dataMatch[1]}`;
    } else if (dataMatch[4]) {
      // YYYY-MM-DD
      dados.data = `${dataMatch[4]}-${dataMatch[5]}-${dataMatch[6]}`;
    }
  }
  
  return dados;
}

function exibirResultadoOCR(dados, imagemBase64, qrcodeTexto = null) {
  document.getElementById('ocrStepProcessando').style.display = 'none';
  document.getElementById('ocrStepResultado').style.display = 'block';
  
  let conteudo = `
    <div class="row mb-3">
      <div class="col-md-6">
        <img src="${imagemBase64}" style="width: 100%; border-radius: 8px; max-height: 300px; object-fit: cover;">
      </div>
      <div class="col-md-6">
        <div class="card bg-light">
          <div class="card-body">
            ${dados.origem === 'QR_CODE' ? '<div class="alert alert-info alert-sm mb-2"><i class="bi bi-qr-code"></i> <strong>QR Code Detectado!</strong></div>' : ''}
            <h6 class="card-title">Dados Extraídos:</h6>
            <table class="table table-sm">
              <tbody>
  `;
  
  if (dados.quantidade_litros) {
    conteudo += `
      <tr>
        <td class="fw-bold">Litros:</td>
        <td class="text-success">${dados.quantidade_litros.toFixed(2)} L</td>
      </tr>
    `;
  } else {
    conteudo += `
      <tr>
        <td class="fw-bold">Litros:</td>
        <td class="text-warning">Não detectado</td>
      </tr>
    `;
  }
  
  if (dados.valor_total) {
    conteudo += `
      <tr>
        <td class="fw-bold">Valor:</td>
        <td class="text-success">R$ ${dados.valor_total.toFixed(2)}</td>
      </tr>
    `;
  } else {
    conteudo += `
      <tr>
        <td class="fw-bold">Valor:</td>
        <td class="text-warning">Não detectado</td>
      </tr>
    `;
  }
  
  if (dados.data) {
    conteudo += `
      <tr>
        <td class="fw-bold">Data:</td>
        <td class="text-success">${new Date(dados.data).toLocaleDateString('pt-BR')}</td>
      </tr>
    `;
  }
  
  conteudo += `
              </tbody>
            </table>
            <small class="text-muted">Revise os dados antes de confirmar</small>
          </div>
        </div>
      </div>
    </div>
  `;
  
  document.getElementById('ocrResultadoConteudo').innerHTML = conteudo;
  
  // Guardar dados para uso posterior
  window.ocrDadosExtraidos = dados;
}

function confirmarDadosOCR() {
  const dados = window.ocrDadosExtraidos;
  
  if (dados.quantidade_litros) {
    document.querySelector('input[name="quantidade_litros"]').value = dados.quantidade_litros.toFixed(2);
  }
  
  if (dados.valor_total) {
    document.querySelector('input[name="valor_total"]').value = dados.valor_total.toFixed(2);
  }
  
  if (dados.data) {
    document.querySelector('input[name="data_abastecimento"]').value = dados.data;
  }
  
  // Fechar modal
  pararCameraCombustivel();
  bootstrap.Modal.getInstance(document.getElementById('ocrCameraModal')).hide();
  
  // Mostrar feedback
  const alert = document.createElement('div');
  alert.className = 'alert alert-success alert-dismissible fade show';
  alert.innerHTML = `
    <i class="bi bi-check-circle"></i> <strong>Dados preenchidos com sucesso!</strong>
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  document.querySelector('form').insertBefore(alert, document.querySelector('form').firstChild);
}

function novaFotoCombustivel() {
  pararCameraCombustivel();
  document.getElementById('ocrStepCamera').style.display = 'block';
  document.getElementById('ocrStepResultado').style.display = 'none';
  iniciarCameraCombustivel();
}

// Adicionar event listeners usando delegação de eventos (para elementos dinâmicos)
document.addEventListener('DOMContentLoaded', function() {
  adicionarListenersCombustivel();
});

// Event delegation para botões dinâmicos
document.addEventListener('click', function(e) {
  if (e.target && e.target.id === 'ocrCapturaBtn') {
    capturarFotoCombustivel();
  } else if (e.target && e.target.id === 'ocrConfirmarBtn') {
    confirmarDadosOCR();
  } else if (e.target && e.target.id === 'ocrNovaFotoBtn') {
    novaFotoCombustivel();
  }
});

function adicionarListenersCombustivel() {
  // Botão de captura
  const capturaBtn = document.getElementById('ocrCapturaBtn');
  if (capturaBtn) {
    capturaBtn.addEventListener('click', capturarFotoCombustivel);
  }
  
  // Botão confirmar
  const confirmarBtn = document.getElementById('ocrConfirmarBtn');
  if (confirmarBtn) {
    confirmarBtn.addEventListener('click', confirmarDadosOCR);
  }
  
  // Botão nova foto
  const novaFotoBtn = document.getElementById('ocrNovaFotoBtn');
  if (novaFotoBtn) {
    novaFotoBtn.addEventListener('click', novaFotoCombustivel);
  }
}

function abrirGaleriaParaOCR() {
  document.getElementById('inputGaleriaOCR').click();
}

function preencherDadosManual() {
  const litros = parseFloat(document.getElementById('manualLitros').value);
  const valor = parseFloat(document.getElementById('manualValor').value);
  const data = document.getElementById('manualData').value;
  
  if (!litros || !valor || !data) {
    alert('Preencha todos os campos obrigatórios');
    return;
  }
  
  // Preencher formulário
  document.querySelector('input[name="quantidade_litros"]').value = litros.toFixed(2);
  document.querySelector('input[name="valor_total"]').value = valor.toFixed(2);
  document.querySelector('input[name="data_abastecimento"]').value = data;
  
  // Mostrar feedback
  const alert = document.createElement('div');
  alert.className = 'alert alert-success alert-dismissible fade show mt-2';
  alert.innerHTML = `
    <i class="bi bi-check-circle"></i> <strong>Dados preenchidos com sucesso!</strong>
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  document.getElementById('ocrTabContent').insertBefore(alert, document.getElementById('ocrTabContent').firstChild);
  
  // Limpar campos manuais
  document.getElementById('manualLitros').value = '';
  document.getElementById('manualValor').value = '';
  document.getElementById('manualData').value = '';
}

function processarImagemGaleria(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  const reader = new FileReader();
  reader.onload = async function(e) {
    const imagemBase64 = e.target.result;
    
    // Mostrar modal
    const modalHtml = `
      <div class="modal fade" id="ocrGaleriaModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Processando Imagem</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <div id="galeriaStepProcessando" style="display: block;">
                <div class="text-center">
                  <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Processando...</span>
                  </div>
                  <p class="text-muted">Analisando imagem... Isso pode levar alguns segundos</p>
                </div>
              </div>
              
              <div id="galeriaStepResultado" style="display: none;">
                <div id="galeriaResultadoConteudo"></div>
                <div class="d-grid gap-2 mt-3">
                  <button class="btn btn-success btn-lg" id="galeriaConfirmarBtn">
                    <i class="bi bi-check-circle"></i> Usar Estes Dados
                  </button>
                  <button class="btn btn-outline-secondary" data-bs-dismiss="modal">Fechar</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    
    if (!document.getElementById('ocrGaleriaModal')) {
      const modalDiv = document.createElement('div');
      modalDiv.innerHTML = modalHtml;
      document.body.appendChild(modalDiv);
    }
    
    const modal = new bootstrap.Modal(document.getElementById('ocrGaleriaModal'));
    modal.show();
    
    // Processar imagem
    await processarOCRCombustivel(imagemBase64);
    
    // Adicionar listener ao botão confirmar
    const confirmarBtn = document.getElementById('galeriaConfirmarBtn');
    if (confirmarBtn) {
      confirmarBtn.onclick = function() {
        confirmarDadosOCR();
        modal.hide();
      };
    }
  };
  
  reader.readAsDataURL(file);
  
  // Resetar input
  event.target.value = '';
}
