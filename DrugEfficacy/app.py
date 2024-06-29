import mysql.connector
import subprocess
import re
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from flask import jsonify
import threading
import tempfile
from werkzeug import utils

app = Flask(__name__, template_folder = '/Users/dylansomra/Desktop/drugEfficacywithownDB/templates')

class App:
    def __init__(self):
        self.processing_status = "not started"
        self.lock = threading.Lock()
        
app.lock = threading.Lock()

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/css/drugefficacystyle.css')
def send_css():
    return send_from_directory('/Users/dylansomra/Desktop/drugEfficacywithownDB/css/',
                               'drugefficacystyle.css')

@app.route("/loading", methods=["GET", "POST"])
def loading():
    if app.processing_status == "finished":
        return redirect("/results")
    else:
        return render_template("loading.html")

@app.route("/check_processing_status", methods=["GET"])
def check_processing_status():
    
    return jsonify({"status": app.processing_status})
    
lock = threading.Lock()

matches = []



def process_file(file):
    global results_key, entity1_names, entity2_names, snps, common_snps, more_common_snps, matches
    
    app.lock.acquire()
    try:
        pharmadb = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            password = 'Strength2000',
            database = 'pharmakg'
            )
        cursor = pharmadb.cursor()
#Connection Confirmation
        if pharmadb.is_connected():
            print("Server Connected")
        else:
            print("Not Connected")
#Returns specific table   
        query = "SELECT * FROM PharmaKGB WHERE Entity1_name IN ('amitriptyline', 'mirtazapine', 'imipramine', 'buproprion', 'nortriptyline') OR Entity2_name IN ('amitriptyline', 'mirtazapine', 'imipramine', 'buproprion', 'nortriptyline') AND Association = 'associated'"
        cursor.execute(query)
        results = cursor.fetchall()
        results_key = []
        entity1_names = []
        entity2_names = []
        snps = []

        for row in results:
            results_key.append(row)
    
        for row in results_key:
            entity1_name = row[2]
            entity2_name = row[5]
            entity1_names.append(entity1_name)
            entity2_names.append(entity2_name)
    
    
        with open(file.filename, "r") as file:
            for line in file:
                match = re.search(r'rs\w+', line)
                if match:
                    rsid = match.group()
            
                    snps.append(rsid)
                    
        
                    
            
        common_snps = set(entity1_names) & set(snps)

        for snp in common_snps:
            for row in results_key:
                if snp == row[2]:
                    match = (snp, row[5])
                    matches.append(match)
            
                    print("SNP:", match[0])
                    print("Entity1:", match[1])
                    
            
        more_common_snps = set(entity2_names) & set(snps)  

        for snp in more_common_snps:
            for row in results_key:
                if snp == row[5]:
                    match = (snp, row[2])
                    matches.append(match)
            
                    print("SNP:", match[0])
                    print("Entity1:", match[1])    
            
        
        print("Number of common SNPs:", len(common_snps))
        print("Number of more common SNPs:", len(more_common_snps))
        print("Number of results:", len(results_key))
        print("Number of Entity1_names:", len(entity1_names))
        print("Number of Entity2_names:", len(entity2_names))
        print("Number of SNPs:", len(snps))
        
        
        
        cursor.close()
        pharmadb.close()
        return matches
    finally:
        app.processing_status = "finished"
        redirect('/results')
        app.lock.release()
        
@app.route("/run_dna_read", methods=["POST"])
def run_dna_read():
    app.processing_status = "processing"
    file = request.files['file']
    
    thread = threading.Thread(target=process_file, args=(file,))
    thread.start()
        
    return redirect("/loading")

def filter_matches_by_entity(matches, search_query):
    filtered_matches = []
    for match in matches:
        if search_query.lower() in match[1].lower():
            filtered_matches.append(match)
    return filtered_matches

@app.route("/results", methods=["POST", "GET"])
def results():
    if request.method == "POST":
        search_query = request.form.get("search_query")
        filtered_matches = filter_matches_by_entity(matches, search_query)
        return render_template("result.html", matches=filtered_matches, search_query=search_query)
    else:
        return render_template("result.html", matches=matches)


if __name__ == "__main__":
    app.run(debug=True)



