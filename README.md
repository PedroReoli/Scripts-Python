# Scripts Python

Repositório de scripts Python para tarefas cotidianas e automações.

## Estrutura

```
scripts/
├── system/     # Scripts relacionados ao sistema
├── utils/      # Utilitários gerais
└── automation/ # Automações
```

## Uso

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar scripts
python scripts/system/system_specs_scanner.py
python scripts/automation/click_automation.py
```

## Scripts Disponíveis

### system_specs_scanner.py
Escaneia especificações do sistema e verifica compatibilidade com requisitos de jogos/modlists.

### click_automation.py
Automação de cliques com interface gráfica:
- Captura coordenadas pressionando a tecla '0'
- Configura múltiplos cliques
- Define delay entre cliques
- Configura repetições do loop e total de execuções
