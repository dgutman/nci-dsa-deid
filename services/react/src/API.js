function makeQueryParams(dict){
    if(dict){
        return '?' + Object.entries(dict).map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`).join('&');
    } else {
        return '';
    }
    
}

class API{

    constructor(url){
        this.endpoint = url; 
    }
    async fetch(queryString, opts = {}, method='GET'){
        const url = this.endpoint+queryString+makeQueryParams(opts.query);
        const headers = {}

        if(localStorage.girderToken){
            headers['Girder-Token'] = localStorage.girderToken;
        }

        if(opts.headers){
            for(const key in opts.headers){
                headers[key] = opts.headers[key]; 
            }
        }
        const responseType = opts.responseType || 'json';
        let body = opts.body;
        if(body && typeof body != 'FormData'){
            delete headers['Content-Type']
            const fd = new FormData();
            for(const key in body){
                const val = typeof body[key] === 'string' ? body[key] : JSON.stringify(body[key]);
                fd.append(key, val)
            }
            body = fd;
        }
        // if json is passed in instead of body, use application/json as the content-type
        if(!body && opts.json){
            headers['Content-Type'] = 'application/json';
            body = typeof opts.json === 'string' ? opts.json : JSON.stringify(opts.json)
        }

        let result = window.fetch(url, {headers, method, body});


        if(opts.log){
            result.then(r => console.log(r));
        }
        const output = {}
        return result.then(resp => {
            output.status = resp.status;
            if(resp.status == 200){
                if(responseType == 'text') {
                    return resp.text();
                } else if (responseType == 'json'){
                    return resp.json();
                }
            } else {
                return resp.statusText;
            }

        }).then(text => {
            output.data = text;
            return output;
        })
            
    }

    async get(queryString, opts){
        return this.fetch(queryString, opts, 'GET');
    }
    async post(queryString, opts){
        return this.fetch(queryString, opts, 'POST');
    }
    async put(queryString, opts){
        return this.fetch(queryString, opts, 'PUT');
    }
    async delete(queryString, opts){
        return this.fetch(queryString, opts, 'DELETE');
    }
    url(path, opts={}){
        return this.endpoint + path +makeQueryParams(opts.query);
    }
}

const api = new API('/dsa/api/v1/'); // TODO: make this configurable via environment variable?

export default api;