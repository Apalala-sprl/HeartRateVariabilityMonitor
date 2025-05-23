# HRV Real-Time Visual App
Monitor your Heart Rate Variability using your Garmin HRM Pro plus sensor


Cette application permet de surveiller en temps réel la variabilité de la fréquence cardiaque (HRV) à l'aide de capteurs BLE comme le Garmin HRM.

## Fonctionnalités
- Détection des capteurs BLE compatibles.
- Affichage des données RR et BPM en temps réel.
- Graphiques dynamiques pour la fréquence cardiaque et le RMSSD.
- Exportation des données au format CSV.

## Prérequis
- Python 3.8 ou supérieur
- Bibliothèques Python : `asyncio`, `tkinter`, `numpy`, `bleak`, `matplotlib`, `pandas`

## Installation
1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/<votre-nom-utilisateur>/HRV-Monitor-App.git
   
2. Installez les dépendances:
   ```bash
   pip install bleak matplotlib pandas

3. Lancez l'application:
   ```bash
   python "Scan Garmin HRM Pro plus.py"

## Capture d'écran
<img width="1280" alt="HRVVisualTool-Screenshot" src="https://github.com/user-attachments/assets/205d6838-5a7e-48d7-b894-791671277507" />
