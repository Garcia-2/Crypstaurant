document.addEventListener("DOMContentLoaded", function () {
    let cart = getCartFromStorage(); // Load cart data from local storage

    // Function to update the cart button
    function updateCartButton() {
        const cartButton = document.getElementById("cart-button");
        const cartCount = cart.length;
        cartButton.textContent = `Cart (${cartCount})`;
    }

    // Function to add product to the cart
    function addToCart(productName, productDescription, productPrice) {
        cart.push({ name: productName, description: productDescription, price: productPrice }); // Add product object to the cart array
        updateCartButton(); // Updating the cart button text
        updateCartInStorage(); // Update cart data in storage
    }

    // Function to remove product from the cart
    function removeFromCart(index) {
        cart.splice(index, 1); // Remove product from the cart array
        updateCartButton(); // Updating the cart button text
        updateCartInStorage(); // Update cart data in storage
    }

    // Function to update cart data in local storage
    function updateCartInStorage() {
        localStorage.setItem("cart", JSON.stringify(cart));
    }

    // Function to retrieve cart data from local storage
    function getCartFromStorage() {
        const storedCart = localStorage.getItem("cart");
        return storedCart ? JSON.parse(storedCart) : [];
    }

    // Event Listener for the 'Order' button on each product
    const orderButtons = document.querySelectorAll(".btn-order");
    orderButtons.forEach((button) => {
        button.addEventListener('click', function (event) {
            const productName = this.getAttribute("data-productName"); // Get product name from a data attribute
            const productDescription = this.getAttribute("data-productDescription"); // Get product name from a data aattribute
            const productPrice = parseFloat(this.getAttribute("data-productPrice")); // Get product price from a data attribute
            addToCart(productName, productDescription, productPrice); // Add product to cart
        });
    });

    // Initialize cart count and update the cart button
    updateCartButton();

    // Example: Add event listener to remove items from cart page
    const removeButtons = document.querySelectorAll(".btn-remove");
    removeButtons.forEach((button, index) => {
        button.addEventListener('click', function (event) {
            removeFromCart(index); // Remove product from the cart

            // Example: Update the cart page here
            const cartItem = button.closest('.cart-item'); // Assuming cart items have a class "cart-item"
            if (cartItem) {
                cartItem.remove(); // Remove the cart item's representation from the page
            }

            // You can also update the total cart price if needed
            const totalCartPrice = calculateTotalCartPrice(); // You need to implement this function
            const totalPriceElement = document.getElementById('total-cart-price');
            if (totalPriceElement) {
                totalPriceElement.textContent = `Total: $${totalCartPrice.toFixed(2)}`;
            }
        });
    });
});
