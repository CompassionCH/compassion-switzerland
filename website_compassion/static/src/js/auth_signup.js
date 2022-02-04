
// Remove password gauge
{
    /*
        observe the field-password element for any new change
        when it encounters a password meter, removes it
    */
    const observer = new MutationObserver((mutations_list) => {
        for(let [i, mutation] of mutations_list.entries()) {
            for(let [i, addedNode] of mutation.addedNodes.entries()) {
                if(addedNode.tagName == "METER") {
                    addedNode.remove();
                }
            }
        }
    });

    observer.observe(document.querySelector(".field-password"), { childList: true });
}