To run this project:

1. Open PowerShell in the project root folder.
2. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Run the app using the venv Python:
   ```powershell
   python -m streamlit run main.py
   ```

If the above command does not work, use the full venv Python path:
```powershell
.\.venv\Scripts\python.exe -m streamlit run main.py
```
