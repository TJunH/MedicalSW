import os
from flask import Flask, render_template,request, jsonify
from SPARQLWrapper import SPARQLWrapper, JSON

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', current_page='home')

@app.route('/about')
def about():
    return render_template('about.html', current_page='about')

@app.route('/disease-list')
def diseaseList():
    page = int(request.args.get('page'))
    size = int(request.args.get('size'))
    totalPage = request.args.get('totalPage')
    q = request.args.get('q')

    sparql = SPARQLWrapper("https://id.nlm.nih.gov/mesh/sparql")
    sparql.addCustomParameter('inference', 'true')
    sparql.setReturnFormat(JSON)

    if q:
        sparql.setQuery(f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
                    
        SELECT DISTINCT (Count(?name) AS ?totalResult) FROM <http://id.nlm.nih.gov/mesh/2024> 
        WHERE {{ 
            ?d a meshv:Descriptor . 
            ?d rdfs:label ?name .
            ?d meshv:treeNumber ?tn .
            FILTER(REGEX(?name,".*{q}.*", "i")) . 
            FILTER(REGEX(?tn,"C")) 
        }}
        """)
        totalResult = int(sparql.query().convert()['results']['bindings'][0]["totalResult"]["value"])
        lastPage = totalResult/size + 1
        
        sparql.setQuery(f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
                        
            SELECT DISTINCT ?d ?name ?tn ?scopeNote FROM <http://id.nlm.nih.gov/mesh/2024>
            WHERE {{ 
            ?d meshv:concept ?concept_o .
            ?concept_o meshv:scopeNote ?scopeNote .
            ?d a meshv:Descriptor . 
            ?d rdfs:label ?name . 
            ?d meshv:treeNumber ?tn .
            FILTER(REGEX(?name, ".*{q}.*", "i")) .
            FILTER(REGEX(?tn, "C"))
        }}
        order by ?name
        offset {(page - 1) * size}
        limit {size}""")
        results = sparql.query().convert()

        jsonResult = []
        for result in results["results"]["bindings"]:
            d_value = result["d"]["value"].split('/')[-1]
            name_value = result["name"]["value"]
            tn_value = result["tn"]["value"].split('/')[-1]
            scopeNote = result["scopeNote"]["value"]
            jsonResult.append({'descr':d_value, 'name':name_value, 'tree':tn_value, 'scopeNote': scopeNote})
        
        return jsonify({'data':jsonResult, 'last_page':lastPage})
    else:
        lastPage = 0
        if totalPage:
            lastPage = totalPage
        else:
            sparql.setQuery(f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
                        
            SELECT DISTINCT (Count(?d) AS ?totalResult) FROM <http://id.nlm.nih.gov/mesh/2024> 
            WHERE {{ 
                ?d a meshv:Descriptor . 
                ?d rdfs:label ?name . 
                ?d meshv:treeNumber ?tn . 
                FILTER(REGEX(?tn,"C..$")) 
            }}
            """)
            totalResult = int(sparql.query().convert()['results']['bindings'][0]["totalResult"]["value"])
            lastPage = totalResult/size + 1
        
        sparql.setQuery(f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
                        
            SELECT DISTINCT ?d ?name ?tn ?scopeNote FROM <http://id.nlm.nih.gov/mesh/2024>
            WHERE {{ 
            ?d meshv:concept ?concept_o .
            ?concept_o meshv:scopeNote ?scopeNote .
            ?d a meshv:Descriptor . 
            ?d rdfs:label ?name . 
            ?d meshv:treeNumber ?tn .
            FILTER(REGEX(?tn, "C..$"))
        }}
        order by ?name
        offset {(page - 1) * size}
        limit {size}""")
        results = sparql.query().convert()

        jsonResult = []
        for result in results["results"]["bindings"]:
            d_value = result["d"]["value"].split('/')[-1]
            name_value = result["name"]["value"]
            tn_value = result["tn"]["value"].split('/')[-1]
            scopeNote = result["scopeNote"]["value"]
            jsonResult.append({'descr':d_value, 'name':name_value, 'tree':tn_value, 'scopeNote': scopeNote})
        
        return jsonify({'data':jsonResult, 'last_page':lastPage})

@app.route('/diseases')
def diseases():
    return render_template('diseases.html', current_page='diseases')

@app.route('/info/<parentTn>')
def info(parentTn):
    sparql = SPARQLWrapper("https://id.nlm.nih.gov/mesh/sparql")
    sparql.addCustomParameter('inference', 'true')
    sparql.setQuery(f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
                    
        SELECT DISTINCT ?d ?name ?tn ?scopeNote FROM <http://id.nlm.nih.gov/mesh/2024>
        WHERE {{
        ?d meshv:concept ?concept_o .
        ?concept_o meshv:scopeNote ?scopeNote .
        ?d a meshv:Descriptor . 
        ?d rdfs:label ?name . 
        ?d meshv:treeNumber ?tn .
        FILTER(REGEX(?tn, "{parentTn}\\\\.\\\\d+$"))
    }}
    order by ?name""")

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    jsonResult = []
    for result in results["results"]["bindings"]:
        d_value = result["d"]["value"].split('/')[-1]
        name_value = result["name"]["value"]
        tn_value = result["tn"]["value"].split('/')[-1]
        scopeNote = result["scopeNote"]['value']
        jsonResult.append({'descr':d_value, 'name':name_value, 'scopeNote': scopeNote, 'tree':tn_value})

    return jsonify({'data':jsonResult})


@app.route('/meds-list')
def medsList():
    page = int(request.args.get('page'))
    size = int(request.args.get('size'))
    totalPage = request.args.get('totalPage')
    q = request.args.get('q')

    sparql = SPARQLWrapper("https://id.nlm.nih.gov/mesh/sparql")
    sparql.addCustomParameter('inference', 'true')
    sparql.setReturnFormat(JSON)

    if q:
        sparql.setQuery(f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
                    
        SELECT DISTINCT (Count(?name) AS ?totalResult) FROM <http://id.nlm.nih.gov/mesh/2024> 
        WHERE {{ 
            ?d a meshv:Descriptor . 
            ?d rdfs:label ?name .
            ?d meshv:treeNumber ?tn .
            FILTER(REGEX(?name,".*{q}.*", "i")) . 
            FILTER(REGEX(?tn,"D")) 
        }}
        """)
        totalResult = int(sparql.query().convert()['results']['bindings'][0]["totalResult"]["value"])
        lastPage = totalResult/size + 1
        
        sparql.setQuery(f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
                        
            SELECT DISTINCT ?d ?name ?tn ?scopeNote FROM <http://id.nlm.nih.gov/mesh/2024>
            WHERE {{ 
            ?d meshv:concept ?concept_o .
            ?concept_o meshv:scopeNote ?scopeNote .
            ?d a meshv:Descriptor . 
            ?d rdfs:label ?name . 
            ?d meshv:treeNumber ?tn .
            FILTER(REGEX(?name, ".*{q}.*", "i")) .
            FILTER(REGEX(?tn, "D"))
        }}
        order by ?name
        offset {(page - 1) * size}
        limit {size}""")
        results = sparql.query().convert()

        jsonResult = []
        for result in results["results"]["bindings"]:
            d_value = result["d"]["value"].split('/')[-1]
            name_value = result["name"]["value"]
            tn_value = result["tn"]["value"].split('/')[-1]
            scopeNote = result["scopeNote"]["value"]
            jsonResult.append({'descr':d_value, 'name':name_value, 'tree':tn_value, 'scopeNote': scopeNote})
        
        return jsonify({'data':jsonResult, 'last_page':lastPage})
    else:
        lastPage = 0
        if totalPage:
            lastPage = totalPage
        else:
            sparql.setQuery(f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
                        
            SELECT DISTINCT (Count(?d) AS ?totalResult) FROM <http://id.nlm.nih.gov/mesh/2024> 
            WHERE {{ 
                ?d a meshv:Descriptor . 
                ?d rdfs:label ?name . 
                ?d meshv:treeNumber ?tn . 
                FILTER(REGEX(?tn,"D..$")) 
            }}
            """)
            totalResult = int(sparql.query().convert()['results']['bindings'][0]["totalResult"]["value"])
            lastPage = totalResult/size + 1
        
        sparql.setQuery(f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
                        
            SELECT DISTINCT ?d ?name ?tn ?scopeNote FROM <http://id.nlm.nih.gov/mesh/2024>
            WHERE {{ 
            ?d meshv:concept ?concept_o .
            ?concept_o meshv:scopeNote ?scopeNote .
            ?d a meshv:Descriptor . 
            ?d rdfs:label ?name . 
            ?d meshv:treeNumber ?tn .
            FILTER(REGEX(?tn, "D..$"))
        }}
        order by ?name
        offset {(page - 1) * size}
        limit {size}""")
        results = sparql.query().convert()

        jsonResult = []
        for result in results["results"]["bindings"]:
            d_value = result["d"]["value"].split('/')[-1]
            name_value = result["name"]["value"]
            tn_value = result["tn"]["value"].split('/')[-1]
            scopeNote = result["scopeNote"]["value"]
            jsonResult.append({'descr':d_value, 'name':name_value, 'tree':tn_value, 'scopeNote': scopeNote})
        
        return jsonify({'data':jsonResult, 'last_page':lastPage})

@app.route('/chemicals-meds')
def chemicalsMeds():
    return render_template('chemicalsMeds.html', current_page='chemicalsMeds')



if __name__=='__main__':
    app.run()
    