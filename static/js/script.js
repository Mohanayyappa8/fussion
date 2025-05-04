document.addEventListener('DOMContentLoaded', function () {

    // Fetch and Show Signature Dishes
    document.getElementById('showSignature').addEventListener('click', function () {
        fetch('/api/signature-dishes')
            .then(response => response.json())
            .then(data => {
                const signatureDishesContainer = document.getElementById('signatureDishes');
                signatureDishesContainer.innerHTML = ''; // Clear previous
                data.forEach(dish => {
                    const dishCard = `
                        <div class="menu-card">
                            <img src="${dish.image_url}" alt="${dish.name}">
                            <h3>${dish.name}</h3>
                            <p>${dish.description}</p>
                            <p>₹${dish.price}</p>
                        </div>
                    `;
                    signatureDishesContainer.innerHTML += dishCard;
                });
                document.getElementById('signaturePopup').style.display = 'block';
            });
    });

    // Fetch and Show Menu Items
    document.getElementById('openMenu').addEventListener('click', function () {
        fetch('/api/menu')
            .then(response => response.json())
            .then(data => {
                const menuItemsContainer = document.getElementById('menuItems');
                menuItemsContainer.innerHTML = ''; // Clear previous
                data.forEach(item => {
                    const itemCard = `
                        <div class="menu-card">
                            <img src="${item.image_url}" alt="${item.name}">
                            <h3>${item.name}</h3>
                            <p>${item.description}</p>
                            <p>₹${item.price}</p>
                        </div>
                    `;
                    menuItemsContainer.innerHTML += itemCard;
                });
                document.getElementById('menuPopup').style.display = 'block';
            });
    });

    // Close Signature Popup
    document.getElementById('closeSignature').addEventListener('click', function () {
        document.getElementById('signaturePopup').style.display = 'none';
    });

    // Close Menu Popup
    document.getElementById('closeMenu').addEventListener('click', function () {
        document.getElementById('menuPopup').style.display = 'none';
    });

    // Close Popup if user clicks outside modal content
    window.addEventListener('click', function (event) {
        if (event.target === document.getElementById('signaturePopup')) {
            document.getElementById('signaturePopup').style.display = 'none';
        }
        if (event.target === document.getElementById('menuPopup')) {
            document.getElementById('menuPopup').style.display = 'none';
        }
    });

});
