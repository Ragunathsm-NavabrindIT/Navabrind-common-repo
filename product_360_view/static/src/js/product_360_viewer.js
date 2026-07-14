/** @odoo-module **/

import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";

export class Product360Viewer extends Component {
    static template = "product_360_view.Viewer";
    static props = {
        imageIds: { type: Array, required: true },
    };

    setup() {
        this.state = useState({
            currentIndex: 0,
            isLoading: true, // Start in loading state
            isDragging: false,
            startX: 0,
        });
        
        // Cache images in browser memory
        this.imageCache = []; 

        onWillStart(async () => {
            await this.preloadImages(this.props.imageIds);
        });

        onWillUpdateProps(async (nextProps) => {
            if (JSON.stringify(nextProps.imageIds) !== JSON.stringify(this.props.imageIds)) {
                await this.preloadImages(nextProps.imageIds);
            }
        });
    }

    async preloadImages(ids) {
        if (!ids || ids.length === 0) {
            this.state.isLoading = false;
            return;
        }

        this.state.isLoading = true;
        this.imageCache = [];
        this.state.currentIndex = 0;

        const promises = ids.map((id) => {
            return new Promise((resolve) => {
                const img = new Image();
                img.src = `/web/image/product.image.360/${id}/image`;
                img.onload = () => resolve();
                img.onerror = () => resolve(); // Resolve even on error to keep going
                this.imageCache.push(img); // Store in memory
            });
        });

        // Wait for all images to download
        await Promise.all(promises);
        this.state.isLoading = false;
    }

    get currentImageSrc() {
        if (!this.props.imageIds || this.props.imageIds.length === 0) {
            return "";
        }
        const imgId = this.props.imageIds[this.state.currentIndex];
        return `/web/image/product.image.360/${imgId}/image`;
    }

    // --- Interaction Handlers ---

    onMouseDown(ev) {
        this.startDrag(ev.clientX);
        window.addEventListener("mousemove", this.onMouseMove);
        window.addEventListener("mouseup", this.onMouseUp);
    }

    onTouchStart(ev) {
        this.startDrag(ev.touches[0].clientX);
        window.addEventListener("touchmove", this.onTouchMove);
        window.addEventListener("touchend", this.onTouchEnd);
    }

    startDrag(clientX) {
        this.state.isDragging = true;
        this.state.startX = clientX;
    }

    handleMove(clientX) {
        if (!this.state.isDragging) return;

        // Sensitivity: Higher number = slower spin. 
        // 5 is very fast, 20 is slow. 10 is balanced.
        const sensitivity = 10; 
        const delta = clientX - this.state.startX;

        if (Math.abs(delta) > sensitivity) {
            const direction = delta > 0 ? -1 : 1; // Drag left vs right
            this.rotate(direction);
            this.state.startX = clientX; 
        }
    }

    rotate(direction) {
        const total = this.props.imageIds.length;
        if (total === 0) return;

        let newIndex = this.state.currentIndex + direction;

        // Infinite Loop Logic
        if (newIndex >= total) newIndex = 0;
        if (newIndex < 0) newIndex = total - 1;

        this.state.currentIndex = newIndex;
    }

    onMouseMove = (ev) => {
        ev.preventDefault();
        this.handleMove(ev.clientX);
    };

    onMouseUp = () => {
        this.stopDrag();
        window.removeEventListener("mousemove", this.onMouseMove);
        window.removeEventListener("mouseup", this.onMouseUp);
    };

    onTouchMove = (ev) => {
        this.handleMove(ev.touches[0].clientX);
    };

    onTouchEnd = () => {
        this.stopDrag();
        window.removeEventListener("touchmove", this.onTouchMove);
        window.removeEventListener("touchend", this.onTouchEnd);
    };

    stopDrag() {
        this.state.isDragging = false;
    }
}