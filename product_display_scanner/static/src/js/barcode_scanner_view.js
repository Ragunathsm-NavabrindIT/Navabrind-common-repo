/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, useRef, useState, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class ScannerView extends Component {
    static template = "product_display_scanner.ScannerView";

    setup() {
        this.orm = useService("orm");
        this.barcodeInput = useRef("barcodeInput");
        this.carouselRef = useRef("carousel3d");
        this.scanDebounceTimeout = null;
        this.activityResetTimeout = null;
        this.autoRotateInterval = null;
        this.retailPricelistId = null;

        this.state = useState({
            product: null,
            notFound: false,
            advertisements: [],
            currentIndex: 0,
        });

        onMounted(() => {
            if (this.barcodeInput.el) {
                this.barcodeInput.el.focus();
            }
            this._loadAdvertisements();
            this._loadRetailPricelistId();
        });

        onWillUnmount(() => {
            clearTimeout(this.scanDebounceTimeout);
            clearTimeout(this.activityResetTimeout);
            clearInterval(this.autoRotateInterval);
        });

        useEffect(
            () => {
                if (this.carouselRef.el && this.state.advertisements.length > 1) {
                    this._updateCarousel();
                    this._startAutoRotation();
                }
                return () => clearInterval(this.autoRotateInterval);
            },
            () => [this.state.advertisements, this.state.currentIndex, this.state.product]
        );
    }

    async _loadRetailPricelistId() {
        const pricelistName = 'Retail Pricelist';
        try {
            const pricelistData = await this.orm.searchRead(
                'product.pricelist',
                [['name', 'ilike', pricelistName]],
                ['id', 'name'],
                { limit: 1 }
            );

            if (pricelistData.length) {
                this.retailPricelistId = pricelistData[0].id;
//                 console.log("✅ Retail Pricelist Found:", pricelistData[0]);
            } else {
//                 console.warn(`⚠️ Pricelist containing '${pricelistName}' not found.`);
                this.retailPricelistId = null;
            }
        } catch (error) {
//             console.error("Error loading Retail Pricelist ID:", error);
            this.retailPricelistId = null;
        }
    }


    _startAutoRotation() {
        clearInterval(this.autoRotateInterval);
        this.autoRotateInterval = setInterval(() => {
            this._next(false);
        }, 5000);
    }

    _resetAutoRotation() {
        clearInterval(this.autoRotateInterval);
        this.autoRotateInterval = setTimeout(() => this._startAutoRotation(), 5000);
    }

    _updateCarousel() {
        if (!this.carouselRef.el) return;
        const slides = this.carouselRef.el.children;
        const totalSlides = slides.length;
        if (totalSlides === 0) return;

        const { currentIndex } = this.state;
        const prevIndex = (currentIndex - 1 + totalSlides) % totalSlides;
        const nextIndex = (currentIndex + 1) % totalSlides;
        const farPrevIndex = (currentIndex - 2 + totalSlides) % totalSlides;
        const farNextIndex = (currentIndex + 2) + totalSlides % totalSlides;

        for (let i = 0; i < totalSlides; i++) {
            const slide = slides[i];
            slide.classList.remove("active", "prev", "next", "far-prev", "far-next");

            if (i === currentIndex) {
                slide.classList.add("active");
            } else if (i === prevIndex) {
                slide.classList.add("prev");
            } else if (i === nextIndex) {
                slide.classList.add("next");
            } else if (totalSlides > 3 && i === farPrevIndex) {
                slide.classList.add("far-prev");
            } else if (totalSlides > 3 && i === farNextIndex) {
                slide.classList.add("far-next");
            }
        }
    }

    _next(userInitiated = true) {
        if (userInitiated) this._resetAutoRotation();
        const totalSlides = this.state.advertisements.length;
        this.state.currentIndex = (this.state.currentIndex + 1) % totalSlides;
    }

    _prev(userInitiated = true) {
        if (userInitiated) this._resetAutoRotation();
        const totalSlides = this.state.advertisements.length;
        this.state.currentIndex = (this.state.currentIndex - 1 + totalSlides) % totalSlides;
    }

    _onSlideClick(index) {
        if (index === this.state.currentIndex) return;
        if (index !== this.state.currentIndex) {
            this._resetAutoRotation();
            this.state.currentIndex = index;
        }
    }

    async _loadAdvertisements() {
        const domain = [['product_tmpl_id.image_128', '!=', false]];
        const fields = ['id', 'display_name', 'default_code'];
        const limit = e;

        try {
            const productCount = await this.orm.searchCount('product.product', domain);
            if (productCount === 0) {
                this.state.advertisements = [];
                return;
            }
            const randomOffsets = new Set();
            const maxCount = Math.min(limit, productCount);
            while (randomOffsets.size < maxCount) {
                randomOffsets.add(Math.floor(Math.random() * productCount));
            }
            const promises = Array.from(randomOffsets).map(offset =>
                this.orm.searchRead('product.product', domain, fields, { limit: 1, offset: offset })
            );
            const results = await Promise.all(promises);
            const adsData = results.flat();
            this.state.advertisements = adsData.map(ad => ({
                ...ad,
                image_url: `/web/image/product.product/${ad.id}/image_1024`,
            }));
        } catch (error) {
//             console.error("Could not load advertisements:", error);
            this.state.advertisements = [];
        }
    }

    _resetToInitialState() {
        this.state.product = null;
        this.state.notFound = false;
        if (this.barcodeInput.el) {
            this.barcodeInput.el.focus();
        }
        if (this.state.advertisements.length > 1) {
            this._startAutoRotation();
        }
    }

    _startResetTimer() {
        clearTimeout(this.activityResetTimeout);
        this.activityResetTimeout = setTimeout(() => this._resetToInitialState(), 30000);
    }

    async _onScan(ev) {
        clearTimeout(this.scanDebounceTimeout);
        clearTimeout(this.activityResetTimeout);
        clearInterval(this.autoRotateInterval);

        const inputElement = ev.target;

        this.scanDebounceTimeout = setTimeout(async () => {
            const barcode = inputElement.value.trim();
            if (!barcode) {
                this._resetToInitialState();
                return;
            }

            const productData = await this.orm.searchRead(
                'product.product',
                [['barcode', '=', barcode]],
                [
                    'id', 'display_name', 'currency_id', 'default_code', 'barcode',
                    'qty_available', 'product_tmpl_id', 'uom_id',
                    'list_price', 'retail_price','secondary_quantity_total'
                ],
                { limit: 1 }
            );

            if (!productData.length) {
                this.state.product = null;
                this.state.notFound = true;
                inputElement.value = "";
                if (this.barcodeInput.el) {
                    this.barcodeInput.el.focus();
                }
                setTimeout(() => {
                    this.state.notFound = false;
                    if (!this.state.product) {
                        this._resetToInitialState();
                    }
                }, 2000);
                return;
            }

            const product = productData[0];
            const currencyInfo = product.currency_id;
            let finalPrice = null;

            try {
                if (product.retail_price && product.retail_price > 0) {
                    finalPrice = product.retail_price;
                } else {
                    // fallback to list price
                    finalPrice = product.list_price || 0;
                }
            } catch (error) {
//                 console.error("Error fetching Retail Price from product:", error);
                finalPrice = product.list_price || 0;
            }

            const priceFormatted = new Intl.NumberFormat(undefined, {
                style: 'currency',
                currency: currencyInfo[1],
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
            }).format(Math.round(finalPrice));

            this.state.product = {
                ...product,
                image_url: `/web/image/product.product/${product.id}/image_1920`,
                price_formatted: priceFormatted,
                retail_price_value: finalPrice,
                uom_name: product.uom_id ? product.uom_id[1] : 'Unit',
            };

            this.state.notFound = false;
            inputElement.value = '';
            this._startResetTimer();
            this.barcodeInput.el.focus();
        }, 400);
    }

}
registry.category("actions").add("product_display_scanner.action", ScannerView);