document.addEventListener('DOMContentLoaded', function() {
    console.log('Page is loaded and ready.');
});

const rectangles = [
    { 
        imageUrl: 'https://www.birds.cornell.edu/home/wp-content/uploads/2023/09/334289821-Baltimore_Oriole-Matthew_Plante.jpg', 
        title: 'Baltimore Oriole',
        description: 'The Baltimore Oriole is a vibrant songbird known for its striking orange and black plumage. These birds are often found in open woodlands, orchards, and suburban areas during the warmer months.' 
    },
    { 
        imageUrl: 'https://example.com/bird2.jpg', 
        title: 'Bird 2', 
        description: 'Bird 2 description.' 
    },
    { 
        imageUrl: 'https://example.com/bird3.jpg', 
        title: 'Bird 3', 
        description: 'Bird 3 description.' 
    },
    { 
        imageUrl: 'https://example.com/bird4.jpg', 
        title: 'Bird 4', 
        description: 'Bird 4 description.' 
    },
    { 
        imageUrl: 'https://example.com/bird5.jpg', 
        title: 'Bird 5', 
        description: 'Bird 5 description.' 
    },
    { 
        imageUrl: 'https://example.com/bird6.jpg', 
        title: 'Bird 6', 
        description: 'Bird 6 description.' 
    },
];

function createRectangles() {
    const scrollableList = document.getElementById('scrollableList');

    rectangles.forEach(rect => {
        const rectangle = document.createElement('div');
        rectangle.className = 'rectangle';

        const img = document.createElement('img');
        img.src = rect.imageUrl;
        img.alt = rect.title;

        const textContainer = document.createElement('div'); // New container for text
        textContainer.className = 'text-container';

        const title = document.createElement('h3'); // Create a title element
        title.textContent = rect.title;

        const text = document.createElement('p');
        text.textContent = rect.description;

        textContainer.appendChild(title);
        textContainer.appendChild(text);
        rectangle.appendChild(img);
        rectangle.appendChild(textContainer); // Append the text container
        scrollableList.appendChild(rectangle);
    });
}


// Call the function to create rectangles on page load
window.onload = createRectangles;
