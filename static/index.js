function confirm_delete() {
    return confirm('Are you sure you want to delete?')
}

$('input[type=password][name=password]').tooltip({
    placement: "right",
    trigger: "focus"
});