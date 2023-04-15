export function custom_apply_patches() {

    console.log("Applying custom JS patches ...");

    String.prototype.startswith = function (prefix, start) {
        //console.log("Custom startswith()! prefix = ", prefix, ", start = ", start);
        var pos_start = (typeof start === 'undefined' ? 0 : start);
        if (prefix instanceof Array) {
            for (var i=0;i<prefix.length;i++) {
                if (this.substring(pos_start, pos_start+prefix[i].length) === prefix [i]) {
                    return true;
                }
            }
        } else {
            return (this.substring(pos_start, pos_start+prefix.length) === prefix);
        }
        return false;
    };
    String.prototype.count = function (ch) {
        var i = 0;
        var count = 0;
        for(; i < this.length; ++i) {
            if (ch == this[i]) {
                ++count;
            }
        }
        return count;
    };
    String.prototype.rjust = function(width, fill_char) {
        if (this.length >= width) {
            return this;
        }
        return fill_char.repeat(width - this.length) + this;
    };


};
