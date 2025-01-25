# Num Piscar de Olhos

**Num Piscar de Olhos** é um sistema desenvolvido para realizar exames de acuidade visual em alunos de escolas públicas, com o objetivo de identificar a necessidade de uso de óculos. Os dados coletados são armazenados para análise e geração de relatórios detalhados.

## 📋 Funcionalidades

- Registro de alunos e seus dados pessoais.
- Realização de exames de acuidade visual:
  - **Exame de Miopia**
  - **Exame de Hipermetropia**
  - **Exame de Astigmatismo**
  - **Exame de Presbiopia**
- Geração de relatórios:
  - Alunos atendidos por escola.
  - Alunos atendidos por Região Administrativa (RA).
- Mapa interativo com escolas atendidas e número de alunos examinados.

## 🛠️ Tecnologias Utilizadas

- **Backend**: PostgreSQL
- **Ferramentas de Desenvolvimento**:
  - SQL Workbench para gerenciamento do banco de dados.
  - GitHub para controle de versão.
- **Linguagens**: SQL, Markdown (para documentação).

## 📂 Estrutura do Banco de Dados

### Tabelas Principais
- `alunos`: Dados dos alunos (nome, idade, RA, etc.).
- `escolas`: Informações das escolas atendidas.
- `exames`: Resultados dos exames realizados.
- `regioes_administrativas`: Dados sobre as Regiões Administrativas.

### Relacionamentos
- Um aluno pertence a uma única escola.
- Uma escola pertence a uma única RA.
- Um exame está associado a um aluno.

## 🚀 Configuração e Instalação

### Requisitos
- **PostgreSQL** instalado.
- SQL Workbench para gerenciar o banco de dados.
- Git instalado para clonar o repositório.

### Passos
1. Clone o repositório:
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd num-piscar-de-olhos