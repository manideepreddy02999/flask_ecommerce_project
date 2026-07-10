
function recalcSelectedTotal() {
    const checkboxes = document.querySelectorAll('.cart-item-checkbox');
    let selectedTotal = 0;
    let selectedCount = 0;

    checkboxes.forEach(cb => {
        const pid = cb.dataset.pid;
        const price = parseInt(cb.dataset.price);

        const qtyEl = document.getElementById(`qty-${pid}`);
        const qty = qtyEl ? parseInt(qtyEl.textContent, 10) : parseInt(cb.dataset.qty, 10);

        const row = document.getElementById(`row-${pid}`);
        if (row) {
            if (cb.checked) {
                row.classList.remove('cart-row--unselected');
            } else {
                row.classList.add('cart-row--unselected');
            }
        }

        if (cb.checked) {
            selectedTotal += price * qty;
            selectedCount++;
        }
    });

    const subtotalEl = document.getElementById('subtotal');
    const grandtotalEl = document.getElementById('grandtotal');
    const selectedCountEl = document.getElementById('selected-count');

    if (subtotalEl) subtotalEl.textContent = '₹' + selectedTotal;
    if (grandtotalEl) grandtotalEl.textContent = '₹' + selectedTotal;
    if (selectedCountEl) {
        const total = checkboxes.length;
        selectedCountEl.textContent = `${selectedCount} of ${total} item${total !== 1 ? 's' : ''} selected`;
    }

    const selectAll = document.getElementById('select-all');
    if (selectAll) {
        selectAll.checked = selectedCount === checkboxes.length && checkboxes.length > 0;
    }
}


function updateCart(pid, action) {
    fetch(`/user/cart/${action}/${pid}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.cart_empty) {
                    window.location.reload();
                    return;
                }

                if (data.removed) {
                    const row = document.getElementById(`row-${pid}`);
                    if (row) row.remove();
                } else {
                    const qtyEl = document.getElementById(`qty-${pid}`);
                    const itemTotalEl = document.getElementById(`item-total-${pid}`);

                    if (qtyEl) qtyEl.textContent = data.quantity;
                    if (itemTotalEl) itemTotalEl.textContent = '₹' + data.item_total;

                    const cb = document.querySelector(`.cart-item-checkbox[data-pid="${pid}"]`);
                    if (cb) cb.dataset.qty = data.quantity;
                }

                recalcSelectedTotal();
            } else {
                console.error('Failed to update cart');
            }
        })
        .catch(error => console.error('Error:', error));
}


document.addEventListener('DOMContentLoaded', function () {

    document.querySelectorAll('.cart-item-checkbox').forEach(cb => {
        cb.addEventListener('change', recalcSelectedTotal);
    });

    const selectAll = document.getElementById('select-all');
    if (selectAll) {
        selectAll.addEventListener('change', function () {
            const checked = this.checked;
            document.querySelectorAll('.cart-item-checkbox').forEach(cb => {
                cb.checked = checked;
            });
            recalcSelectedTotal();
        });
    }

    recalcSelectedTotal();

    const btnCheckout = document.getElementById('btn-proceed-checkout');
    if (btnCheckout) {
        btnCheckout.addEventListener('click', function (e) {
            e.preventDefault();
            const checkedBoxes = document.querySelectorAll('.cart-item-checkbox:checked');
            if (checkedBoxes.length === 0) {
                alert("Please select at least one item to checkout.");
                return;
            }

            const items = [];
            checkedBoxes.forEach(cb => {
                items.push({
                    pid: cb.dataset.pid,
                    price: parseInt(cb.dataset.price),
                    quantity: parseInt(cb.dataset.qty, 10),
                    name: cb.dataset.name,
                    image: cb.dataset.image
                });
            });

            fetch('/user/cart/checkout_selection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ items: items })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = '/user/checkout';
                    } else {
                        alert(data.message || "Failed to proceed to checkout.");
                    }
                })
                .catch(error => {
                    console.error("Checkout error:", error);
                    alert("Something went wrong.");
                });
        });
    }
});