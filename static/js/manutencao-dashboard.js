// Dashboard Inteligente para Manutenção
document.addEventListener('DOMContentLoaded', function() {
    const selectVeiculo = document.getElementById('selectVeiculo');
    const selectTipoManutencao = document.getElementById('selectTipoManutencao');
    const selectPeca = document.getElementById('selectPeca');
    const inputQuilometragem = document.getElementById('inputQuilometragem');
    const inputVidaUtil = document.getElementById('inputVidaUtil');
    const inputProximaManutencao = document.getElementById('inputProximaManutencao');
    const inputValorPeca = document.getElementById('inputValorPeca');
    const inputValorMaoObra = document.getElementById('inputValorMaoObra');
    const inputObservacoes = document.getElementById('inputObservacoes');
    const btnRapido = document.getElementById('btnRapido');

    // Tipos de manutenção mais comuns
    const tiposManutencao = [
        { tipo: 'Troca de Óleo', vida_util: 10000, proxima_manutencao: 5000 },
        { tipo: 'Troca de Filtros', vida_util: 15000, proxima_manutencao: 10000 },
        { tipo: 'Troca de Pastilhas de Freio', vida_util: 20000, proxima_manutencao: 15000 },
        { tipo: 'Troca de Pneus', vida_util: 40000, proxima_manutencao: 30000 },
        { tipo: 'Troca de Velas', vida_util: 30000, proxima_manutencao: 20000 },
        { tipo: 'Troca de Correia', vida_util: 25000, proxima_manutencao: 15000 },
        { tipo: 'Troca de Bateria', vida_util: 60000, proxima_manutencao: 40000 },
        { tipo: 'Troca de Embreagem', vida_util: 35000, proxima_manutencao: 25000 },
        { tipo: 'Alinhamento e Balanceamento', vida_util: 20000, proxima_manutencao: 20000 },
        { tipo: 'Revisão Completa', vida_util: 50000, proxima_manutencao: 50000 }
    ];

    // Peças mais comuns
    const pecasComuns = [
        'Óleo Motor',
        'Filtro de Óleo',
        'Filtro de Ar',
        'Filtro de Combustível',
        'Pastilhas de Freio Dianteiras',
        'Pastilhas de Freio Traseiras',
        'Disco de Freio',
        'Pneu Dianteiro Esquerdo',
        'Pneu Dianteiro Direito',
        'Pneu Traseiro Esquerdo',
        'Pneu Traseiro Direito',
        'Velas de Ignição',
        'Correia Dentada',
        'Correia Estriada',
        'Bateria',
        'Amortecedor Dianteiro Esquerdo',
        'Amortecedor Dianteiro Direito',
        'Amortecedor Traseiro Esquerdo',
        'Amortecedor Traseiro Direito',
        'Embreagem',
        'Fluido de Freio',
        'Fluido de Direção Hidráulica',
        'Fluido de Arrefecimento',
        'Radiador',
        'Alternador',
        'Bomba de Combustível',
        'Injetores',
        'Catalisador'
    ];

    // Preencher select de tipos de manutenção
    if (selectTipoManutencao) {
        tiposManutencao.forEach(function(tipo) {
            const option = document.createElement('option');
            option.value = tipo.tipo;
            option.textContent = tipo.tipo;
            selectTipoManutencao.appendChild(option);
        });
    }

    // Preencher select de peças
    if (selectPeca) {
        pecasComuns.forEach(function(peca) {
            const option = document.createElement('option');
            option.value = peca;
            option.textContent = peca;
            selectPeca.appendChild(option);
        });
    }

    // Evento de mudança no tipo de manutenção
    if (selectTipoManutencao) {
        selectTipoManutencao.addEventListener('change', function() {
            const tipoSelecionado = tiposManutencao.find(function(t) {
                return t.tipo === this.value;
            });

            if (tipoSelecionado) {
                if (inputVidaUtil) {
                    inputVidaUtil.value = tipoSelecionado.vida_util;
                }
                if (inputProximaManutencao) {
                    inputProximaManutencao.value = tipoSelecionado.proxima_manutencao;
                }
            }
        });
    }

    // Evento de mudança na peça
    if (selectPeca) {
        selectPeca.addEventListener('change', function() {
            // Sugestões de valores baseadas na peça selecionada
            const peca = this.value;
            let valorSugerido = 0;
            let valorMaoObraSugerido = 0;

            switch(peca) {
                case 'Óleo Motor':
                    valorSugerido = 80;
                    valorMaoObraSugerido = 50;
                    break;
                case 'Filtro de Óleo':
                case 'Filtro de Ar':
                case 'Filtro de Combustível':
                    valorSugerido = 30;
                    valorMaoObraSugerido = 20;
                    break;
                case 'Pastilhas de Freio Dianteiras':
                case 'Pastilhas de Freio Traseiras':
                    valorSugerido = 150;
                    valorMaoObraSugerido = 80;
                    break;
                case 'Disco de Freio':
                    valorSugerido = 200;
                    valorMaoObraSugerido = 100;
                    break;
                case 'Pneu Dianteiro Esquerdo':
                case 'Pneu Dianteiro Direito':
                case 'Pneu Traseiro Esquerdo':
                case 'Pneu Traseiro Direito':
                    valorSugerido = 400;
                    valorMaoObraSugerido = 150;
                    break;
                case 'Velas de Ignição':
                    valorSugerido = 40;
                    valorMaoObraSugerido = 30;
                    break;
                case 'Correia Dentada':
                case 'Correia Estriada':
                    valorSugerido = 60;
                    valorMaoObraSugerido = 40;
                    break;
                case 'Bateria':
                    valorSugerido = 350;
                    valorMaoObraSugerido = 100;
                    break;
                case 'Amortecedor Dianteiro Esquerdo':
                case 'Amortecedor Dianteiro Direito':
                case 'Amortecedor Traseiro Esquerdo':
                case 'Amortecedor Traseiro Direito':
                    valorSugerido = 250;
                    valorMaoObraSugerido = 150;
                    break;
                case 'Embreagem':
                    valorSugerido = 300;
                    valorMaoObraSugerido = 200;
                    break;
                case 'Fluido de Freio':
                case 'Fluido de Direção Hidráulica':
                case 'Fluido de Arrefecimento':
                    valorSugerido = 50;
                    valorMaoObraSugerido = 40;
                    break;
                case 'Radiador':
                    valorSugerido = 200;
                    valorMaoObraSugerido = 100;
                    break;
                case 'Alternador':
                    valorSugerido = 400;
                    valorMaoObraSugerido = 150;
                    break;
                case 'Bomba de Combustível':
                    valorSugerido = 350;
                    valorMaoObraSugerido = 200;
                    break;
                case 'Injetores':
                    valorSugerido = 600;
                    valorMaoObraSugerido = 300;
                    break;
                case 'Catalisador':
                    valorSugerido = 500;
                    valorMaoObraSugerido = 250;
                    break;
            }

            if (inputValorPeca) {
                inputValorPeca.value = valorSugerido;
            }
            if (inputValorMaoObra) {
                inputValorMaoObra.value = valorMaoObraSugerido;
            }
        });
    }

    // Botão de cadastro rápido
    if (btnRapido) {
        btnRapido.addEventListener('click', function() {
            // Preencher campos com valores padrão
            if (selectTipoManutencao) {
                selectTipoManutencao.selectedIndex = 0;
                selectTipoManutencao.dispatchEvent(new Event('change'));
            }
            if (selectPeca) {
                selectPeca.selectedIndex = 0;
                selectPeca.dispatchEvent(new Event('change'));
            }
            if (inputQuilometragem) {
                inputQuilometragem.value = '';
                inputQuilometragem.focus();
            }
            if (inputObservacoes) {
                inputObservacoes.value = 'Manutenção preventiva realizada conforme recomendação do fabricante.';
            }
        });
    }
});
