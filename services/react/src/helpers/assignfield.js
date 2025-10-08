function readNested(obj, field){
    return field.split('.').reduce((obj, key) => {
        return obj ? (key in obj ? obj[key] : undefined) : undefined
    }, obj)
}

function assignNested(obj, field, val){
    return field.split('.').reduce( (obj, key, index, fields)=>{
        if(index < fields.length-1){
            // not the final field; return the sub object
            if(!(key in obj)){
                obj[key] = {};
            }
            return obj[key];
        }
        obj[key] = val;
        return obj;
    }, obj);
}

export  { readNested, assignNested };