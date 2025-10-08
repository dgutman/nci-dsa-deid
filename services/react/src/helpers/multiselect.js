function getMultiselectValues(select){
    return Array.from(select.childNodes).reduce((arr,opt)=>{
        if(opt.selected) arr.push(opt.value||opt.text); 
        return arr;
    },[])
}

export { getMultiselectValues }