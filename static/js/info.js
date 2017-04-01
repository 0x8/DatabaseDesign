$(document).ready(function() {
    function deleteAllChildren(node) {
        while (node.hasChildNodes()) {
            node.removeChild(node.lastChild);
        }
    }

    $('#query-selector').on('change', function() {
        deleteAllChildren($('#query-extra')[0]);
        target = $(`#query-extra-storage span[data-query-type="${this.value}"]`);
        console.log(target);
        target.clone().appendTo('#query-extra');
    });
});
