
// thanks https://stackoverflow.com/a/43963612/1694896

export var fn_unique_object_id = (() => {
    let currentId = 0;
    const map = new WeakMap();
    
    return (object) => {
        if (!map.has(object)) {
            map.set(object, ++currentId);
        }
        
        return map.get(object);
    };
})();
