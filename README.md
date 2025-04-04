# Apache Superset - Fork de TawanMd

Este é um fork do repositório oficial `apache/superset`.

## Configuração do Ambiente de Desenvolvimento (Ubuntu 24.04 LTS / WSL 2)

Estas instruções detalham como configurar um ambiente de desenvolvimento local para rodar o Superset diretamente a partir deste código fonte, permitindo modificações e testes. Ambiente testado: Ubuntu 24.04 LTS rodando no WSL 2.

### Pré-requisitos

*   Windows 10/11 com WSL 2 configurado.
*   Ubuntu 24.04 LTS instalado no WSL 2.
*   Git (`sudo apt install git`).
*   `curl` (`sudo apt install curl`).
*   `openssl` (geralmente padrão no Ubuntu).
*   Conexão com a internet.
*   (Opcional, mas recomendado): Diretório `~/superset-install` para guardar o venv e config (ou ajuste os paths abaixo).

### Passos Detalhados

1.  **Clonar este Repositório (Fork):**
    ```bash
    cd ~ # Ir para o diretório home
    git clone https://github.com/TawanMd/superset-ubuntu.git superset-source-code
    cd superset-source-code
    ```

2.  **Instalar Dependências do Sistema Operacional:**
    ```bash
    sudo apt update && sudo apt upgrade -y
    # Ferramentas de compilação, Python 3.10, libs para DBs, libs LDAP/SASL, zstd, e para add-apt-repo
    sudo apt install -y build-essential pkg-config libssl-dev libffi-dev \
                      python3.10 python3.10-dev python3.10-venv \
                      default-libmysqlclient-dev libpq-dev \
                      libldap2-dev libsasl2-dev \
                      zstd \
                      software-properties-common curl
    # (Opcional, necessário se python3.10 não estiver nos repos padrão) Adicionar PPA e instalar
    # sudo add-apt-repository ppa:deadsnakes/ppa
    # sudo apt update
    # sudo apt install -y python3.10 python3.10-dev python3.10-venv
    ```

3.  **Configurar Node.js via `nvm` (Node Version Manager):**
    *   Instalar `nvm`:
        ```bash
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
        ```
    *   **FECHE E REABRA O TERMINAL.**
    *   Verificar instalação `nvm`: `command -v nvm` (deve retornar `nvm`)
    *   Navegar para a raiz do projeto e instalar a versão do Node definida no `.nvmrc`:
        ```bash
        cd ~/superset-source-code # Garantir que está na raiz
        # Se o .nvmrc não estiver na raiz, mova-o (verificar localização no repo):
        # git mv path/to/.nvmrc . && git commit -m "Mover .nvmrc" && git push
        nvm install # Lê .nvmrc e instala a versão Node/npm correta
        nvm use     # Ativa a versão instalada
        node --version && npm --version # Verificar
        ```

4.  **Criar e Ativar Ambiente Virtual Python:**
    *   Usaremos um diretório separado para o venv para mantê-lo fora do repo git do código fonte.
        ```bash
        mkdir -p ~/superset-install
        cd ~/superset-install # Ir para a pasta de instalação/config
        python3.10 -m venv venv
        source venv/bin/activate # Ativar o venv
        ```

5.  **Instalar Dependências Python (Desenvolvimento):**
    *   Voltar para o diretório do código fonte e instalar requirements:
        ```bash
        cd ~/superset-source-code # Voltar para o código fonte
        pip install --upgrade pip setuptools wheel # Atualizar pip no venv
        pip install -r requirements/base.txt
        # Usamos 'development.txt', ajuste se o nome for outro
        pip install -r requirements/development.txt
        ```

6.  **Instalar Superset em Modo Editável:**
    *   Com o venv ativo e no diretório `~/superset-source-code`:
        ```bash
        pip install -e .
        ```

7.  **Construir Ativos do Frontend:**
    *   Verificar `npm` (já deve estar ok via `nvm`).
    *   Navegar para a pasta frontend, instalar dependências e construir:
        ```bash
        cd superset-frontend
        # Limpar antes é uma boa ideia, especialmente após erros
        # rm -rf node_modules
        npm install # Usar npm install após limpeza ou se 'ci' falhar (PODE DEMORAR)
        npm run build # Construir ativos (PODE DEMORAR)
        cd .. # Voltar para ~/superset-source-code
        ```

8.  **Configurar `superset_config.py` (com `SECRET_KEY`):**
    *   Gere uma chave segura:
        ```bash
        openssl rand -base64 42
        ```
    *   Copie a chave gerada.
    *   Crie/Edite o arquivo de configuração (vamos colocá-lo em `superset-install`):
        ```bash
        nano ~/superset-install/superset_config.py
        ```
    *   Adicione o seguinte conteúdo, substituindo o placeholder pela sua chave:
        ```python
        # superset_config.py
        SECRET_KEY = 'SUA_CHAVE_SECRETA_ALEATORIA_AQUI'
        # Adicione outras configurações personalizadas aqui, se necessário
        ```
    *   Salve e feche (`Ctrl+X`, `Y`, `Enter`).

9.  **Definir Variáveis de Ambiente:**
    *   (Com venv ativo)
        ```bash
        export FLASK_APP=superset
        export SUPERSET_CONFIG_PATH=~/superset-install/superset_config.py
        ```

10. **Inicializar Banco de Dados e Roles:**
    ```bash
    superset db upgrade
    # Crie o admin se ainda não o fez neste DB (omitido se já existe do setup anterior)
    # superset fab create-admin
    superset init
    ```

### Rodando o Servidor de Desenvolvimento

1.  Navegue para o diretório do código fonte: `cd ~/superset-source-code`
2.  Ative o ambiente virtual: `source ~/superset-install/venv/bin/activate`
3.  Exporte as variáveis de ambiente:
    ```bash
    export FLASK_APP=superset
    export SUPERSET_CONFIG_PATH=~/superset-install/superset_config.py
    ```
4.  Inicie o servidor:
    ```bash
    superset run -p 8088 --with-threads --reload --debugger
    ```
5.  Acesse `http://localhost:8088` no navegador do Windows.

### Modificando o Código

*   **Backend:** Edite os arquivos Python dentro de `~/superset-source-code/superset/`. As alterações terão efeito após reiniciar o servidor (`Ctrl+C` e `superset run...`).
*   **Frontend:** Edite os arquivos em `~/superset-source-code/superset-frontend/`. Após salvar, você precisará reconstruir os ativos:
    ```bash
    cd ~/superset-source-code/superset-frontend
    npm run build
    cd ..
    # Reinicie o servidor Superset
    ```
    *(Alternativamente, rode `npm run dev` em um terminal separado para rebuild automático do frontend).*
*   **Versionamento:** Use `git add`, `git commit`, `git push` dentro de `~/superset-source-code` para enviar suas modificações para o seu fork `TawanMd/superset-ubuntu`.

<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Superset

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/license/apache-2-0)
[![Latest Release on Github](https://img.shields.io/github/v/release/apache/superset?sort=semver)](https://github.com/apache/superset/releases/latest)
[![Build Status](https://github.com/apache/superset/actions/workflows/superset-python-unittest.yml/badge.svg)](https://github.com/apache/superset/actions)
[![PyPI version](https://badge.fury.io/py/apache_superset.svg)](https://badge.fury.io/py/apache_superset)
[![Coverage Status](https://codecov.io/github/apache/superset/coverage.svg?branch=master)](https://codecov.io/github/apache/superset)
[![PyPI](https://img.shields.io/pypi/pyversions/apache_superset.svg?maxAge=2592000)](https://pypi.python.org/pypi/apache_superset)
[![Get on Slack](https://img.shields.io/badge/slack-join-orange.svg)](http://bit.ly/join-superset-slack)
[![Documentation](https://img.shields.io/badge/docs-apache.org-blue.svg)](https://superset.apache.org)

<picture width="500">
  <source
    width="600"
    media="(prefers-color-scheme: dark)"
    src="https://superset.apache.org/img/superset-logo-horiz-dark.svg"
    alt="Superset logo (dark)"
  />
  <img
    width="600"
    src="https://superset.apache.org/img/superset-logo-horiz-apache.svg"
    alt="Superset logo (light)"
  />
</picture>

A modern, enterprise-ready business intelligence web application.

[**Why Superset?**](#why-superset) |
[**Supported Databases**](#supported-databases) |
[**Installation and Configuration**](#installation-and-configuration) |
[**Release Notes**](https://github.com/apache/superset/blob/master/RELEASING/README.md#release-notes-for-recent-releases) |
[**Get Involved**](#get-involved) |
[**Contributor Guide**](#contributor-guide) |
[**Resources**](#resources) |
[**Organizations Using Superset**](https://github.com/apache/superset/blob/master/RESOURCES/INTHEWILD.md)

## Why Superset?

Superset is a modern data exploration and data visualization platform. Superset can replace or augment proprietary business intelligence tools for many teams. Superset integrates well with a variety of data sources.

Superset provides:

- A **no-code interface** for building charts quickly
- A powerful, web-based **SQL Editor** for advanced querying
- A **lightweight semantic layer** for quickly defining custom dimensions and metrics
- Out of the box support for **nearly any SQL** database or data engine
- A wide array of **beautiful visualizations** to showcase your data, ranging from simple bar charts to geospatial visualizations
- Lightweight, configurable **caching layer** to help ease database load
- Highly extensible **security roles and authentication** options
- An **API** for programmatic customization
- A **cloud-native architecture** designed from the ground up for scale

## Screenshots & Gifs

**Video Overview**

<!-- File hosted here https://github.com/apache/superset-site/raw/lfs/superset-video-4k.mp4 -->

[superset-video-1080p.webm](https://github.com/user-attachments/assets/b37388f7-a971-409c-96a7-90c4e31322e6)

<br/>

**Large Gallery of Visualizations**

<kbd><img title="Gallery" src="https://superset.apache.org/img/screenshots/gallery.jpg"/></kbd><br/>

**Craft Beautiful, Dynamic Dashboards**

<kbd><img title="View Dashboards" src="https://superset.apache.org/img/screenshots/slack_dash.jpg"/></kbd><br/>

**No-Code Chart Builder**

<kbd><img title="Slice & dice your data" src="https://superset.apache.org/img/screenshots/explore.jpg"/></kbd><br/>

**Powerful SQL Editor**

<kbd><img title="SQL Lab" src="https://superset.apache.org/img/screenshots/sql_lab.jpg"/></kbd><br/>

## Supported Databases

Superset can query data from any SQL-speaking datastore or data engine (Presto, Trino, Athena, [and more](https://superset.apache.org/docs/configuration/databases)) that has a Python DB-API driver and a SQLAlchemy dialect.

Here are some of the major database solutions that are supported:

<p align="center">
  <img src="https://superset.apache.org/img/databases/redshift.png" alt="redshift" border="0" width="200"/>
  <img src="https://superset.apache.org/img/databases/google-biquery.png" alt="google-biquery" border="0" width="200"/>
  <img src="https://superset.apache.org/img/databases/snowflake.png" alt="snowflake" border="0" width="200"/>
  <img src="https://superset.apache.org/img/databases/trino.png" alt="trino" border="0" width="150" />
  <img src="https://superset.apache.org/img/databases/presto.png" alt="presto" border="0" width="200"/>
  <img src="https://superset.apache.org/img/databases/databricks.png" alt="databricks" border="0" width="160" />
  <img src="https://superset.apache.org/img/databases/druid.png" alt="druid" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/firebolt.png" alt="firebolt" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/timescale.png" alt="timescale" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/rockset.png" alt="rockset" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/postgresql.png" alt="postgresql" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/mysql.png" alt="mysql" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/mssql-server.png" alt="mssql-server" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/ibm-db2.svg" alt="db2" border="0" width="220" />
  <img src="https://superset.apache.org/img/databases/sqlite.png" alt="sqlite" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/sybase.png" alt="sybase" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/mariadb.png" alt="mariadb" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/vertica.png" alt="vertica" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/oracle.png" alt="oracle" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/firebird.png" alt="firebird" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/greenplum.png" alt="greenplum" border="0" width="200"  />
  <img src="https://superset.apache.org/img/databases/clickhouse.png" alt="clickhouse" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/exasol.png" alt="exasol" border="0" width="160" />
  <img src="https://superset.apache.org/img/databases/monet-db.png" alt="monet-db" border="0" width="200"  />
  <img src="https://superset.apache.org/img/databases/apache-kylin.png" alt="apache-kylin" border="0" width="80"/>
  <img src="https://superset.apache.org/img/databases/hologres.png" alt="hologres" border="0" width="80"/>
  <img src="https://superset.apache.org/img/databases/netezza.png" alt="netezza" border="0" width="80"/>
  <img src="https://superset.apache.org/img/databases/pinot.png" alt="pinot" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/teradata.png" alt="teradata" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/yugabyte.png" alt="yugabyte" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/databend.png" alt="databend" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/starrocks.png" alt="starrocks" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/doris.png" alt="doris" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/oceanbase.svg" alt="oceanbase" border="0" width="220" />
  <img src="https://superset.apache.org/img/databases/sap-hana.png" alt="oceanbase" border="0" width="220" />
  <img src="https://superset.apache.org/img/databases/denodo.png" alt="denodo" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/ydb.svg" alt="ydb" border="0" width="200" />
  <img src="https://superset.apache.org/img/databases/tdengine.png" alt="TDengine" border="0" width="200" />
</p>

**A more comprehensive list of supported databases** along with the configuration instructions can be found [here](https://superset.apache.org/docs/configuration/databases).

Want to add support for your datastore or data engine? Read more [here](https://superset.apache.org/docs/frequently-asked-questions#does-superset-work-with-insert-database-engine-here) about the technical requirements.

## Installation and Configuration

Try out Superset's [quickstart](https://superset.apache.org/docs/quickstart/) guide or learn about [the options for production deployments](https://superset.apache.org/docs/installation/architecture/).

## Get Involved

- Ask and answer questions on [StackOverflow](https://stackoverflow.com/questions/tagged/apache-superset) using the **apache-superset** tag
- [Join our community's Slack](http://bit.ly/join-superset-slack)
  and please read our [Slack Community Guidelines](https://github.com/apache/superset/blob/master/CODE_OF_CONDUCT.md#slack-community-guidelines)
- [Join our dev@superset.apache.org Mailing list](https://lists.apache.org/list.html?dev@superset.apache.org). To join, simply send an email to [dev-subscribe@superset.apache.org](mailto:dev-subscribe@superset.apache.org)
- If you want to help troubleshoot GitHub Issues involving the numerous database drivers that Superset supports, please consider adding your name and the databases you have access to on the [Superset Database Familiarity Rolodex](https://docs.google.com/spreadsheets/d/1U1qxiLvOX0kBTUGME1AHHi6Ywel6ECF8xk_Qy-V9R8c/edit#gid=0)
- Join Superset's Town Hall and [Operational Model](https://preset.io/blog/the-superset-operational-model-wants-you/) recurring meetings. Meeting info is available on the [Superset Community Calendar](https://superset.apache.org/community)

## Contributor Guide

Interested in contributing? Check out our
[CONTRIBUTING.md](https://github.com/apache/superset/blob/master/CONTRIBUTING.md)
to find resources around contributing along with a detailed guide on
how to set up a development environment.

## Resources

- [Superset "In the Wild"](https://github.com/apache/superset/blob/master/RESOURCES/INTHEWILD.md) - open a PR to add your org to the list!
- [Feature Flags](https://github.com/apache/superset/blob/master/RESOURCES/FEATURE_FLAGS.md) - the status of Superset's Feature Flags.
- [Standard Roles](https://github.com/apache/superset/blob/master/RESOURCES/STANDARD_ROLES.md) - How RBAC permissions map to roles.
- [Superset Wiki](https://github.com/apache/superset/wiki) - Tons of additional community resources: best practices, community content and other information.
- [Superset SIPs](https://github.com/orgs/apache/projects/170) - The status of Superset's SIPs (Superset Improvement Proposals) for both consensus and implementation status.

Understanding the Superset Points of View

- [The Case for Dataset-Centric Visualization](https://preset.io/blog/dataset-centric-visualization/)
- [Understanding the Superset Semantic Layer](https://preset.io/blog/understanding-superset-semantic-layer/)

- Getting Started with Superset
  - [Superset in 2 Minutes using Docker Compose](https://superset.apache.org/docs/installation/docker-compose#installing-superset-locally-using-docker-compose)
  - [Installing Database Drivers](https://superset.apache.org/docs/configuration/databases#installing-database-drivers)
  - [Building New Database Connectors](https://preset.io/blog/building-database-connector/)
  - [Create Your First Dashboard](https://superset.apache.org/docs/using-superset/creating-your-first-dashboard/)
  - [Comprehensive Tutorial for Contributing Code to Apache Superset
    ](https://preset.io/blog/tutorial-contributing-code-to-apache-superset/)
- [Resources to master Superset by Preset](https://preset.io/resources/)

- Deploying Superset

  - [Official Docker image](https://hub.docker.com/r/apache/superset)
  - [Helm Chart](https://github.com/apache/superset/tree/master/helm/superset)

- Recordings of Past [Superset Community Events](https://preset.io/events)

  - [Mixed Time Series Charts](https://preset.io/events/mixed-time-series-visualization-in-superset-workshop/)
  - [How the Bing Team Customized Superset for the Internal Self-Serve Data & Analytics Platform](https://preset.io/events/how-the-bing-team-heavily-customized-superset-for-their-internal-data/)
  - [Live Demo: Visualizing MongoDB and Pinot Data using Trino](https://preset.io/events/2021-04-13-visualizing-mongodb-and-pinot-data-using-trino/)
  - [Introduction to the Superset API](https://preset.io/events/introduction-to-the-superset-api/)
  - [Building a Database Connector for Superset](https://preset.io/events/2021-02-16-building-a-database-connector-for-superset/)

- Visualizations

  - [Creating Viz Plugins](https://superset.apache.org/docs/contributing/creating-viz-plugins/)
  - [Managing and Deploying Custom Viz Plugins](https://medium.com/nmc-techblog/apache-superset-manage-custom-viz-plugins-in-production-9fde1a708e55)
  - [Why Apache Superset is Betting on Apache ECharts](https://preset.io/blog/2021-4-1-why-echarts/)

- [Superset API](https://superset.apache.org/docs/rest-api)

## Repo Activity

<a href="https://next.ossinsight.io/widgets/official/compose-last-28-days-stats?repo_id=39464018" target="_blank" align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://next.ossinsight.io/widgets/official/compose-last-28-days-stats/thumbnail.png?repo_id=39464018&image_size=auto&color_scheme=dark" width="655" height="auto" />
    <img alt="Performance Stats of apache/superset - Last 28 days" src="https://next.ossinsight.io/widgets/official/compose-last-28-days-stats/thumbnail.png?repo_id=39464018&image_size=auto&color_scheme=light" width="655" height="auto" />
  </picture>
</a>

<!-- Made with [OSS Insight](https://ossinsight.io/) -->

<!-- telemetry/analytics pixel: -->
<img referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=bc1c90cd-bc04-4e11-8c7b-289fb2839492" />
