import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Product, Deal, productService } from '@/api/';

interface ProductPreviewData {
  product: Product;
  related_products: Product[];
  deal: Deal | null;
}

const ProductDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [productData, setProductData] = useState<ProductPreviewData | null>(null);
  const [quantity, setQuantity] = useState(1);

  useEffect(() => {
    const fetchProductData = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        const data = await productService.getProductPreview(Number(id));
        setProductData(data);
        setError(null);
        
        // Increment view count
        productService.incrementViewCount(Number(id));
      } catch (err) {
        setError('Failed to load product details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchProductData();
  }, [id]);

  const handleQuantityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setQuantity(Number(e.target.value));
  };

  const handleAddToCart = () => {
    alert(`Added ${quantity} item(s) to cart`);
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading product details...</div>;
  }

  if (error || !productData) {
    return <div className="text-red-500 text-center">{error || 'Product not found'}</div>;
  }

  const { product, related_products, deal } = productData;

  return (
    <div className="container mx-auto px-4 py-8"></div>
      <div className="bg-white shadow-lg rounded-lg overflow-hidden">
        <div className="md:flex">
          <div className="md:w-1/2 bg-gray-100">
            {product.image_url ? (
              <img src={product.image_url} alt={product.name} className="w-full h-96 object-contain p-4" />
            ) : (
              <div className="w-full h-96 flex items-center justify-center bg-gray-200">
                <span className="text-xl text-gray-500">No Image</span>
              </div>
            )}
          </div>

          <div className="md:w-1/2 p-6">
            <div className="flex justify-between items-start"></div>
              <h1 className="text-3xl font-bold text-gray-800">{product.name}</h1>
              {product.is_featured && (
                <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                  Featured
                </span>
              )}
            </div>

            <Link to={`/shop/${product.shop}`} className="inline-block mt-2 text-blue-600 hover:underline">
              By {product.shop_name}
            </Link>

            <div className="mt-4">
              {product.discount_percentage > 0 ? (
                <div className="flex items-center">
                  <p className="text-gray-400 line-through text-xl">${product.price}</p>
                  <p className="ml-2 text-3xl font-bold text-green-600">${product.discounted_price}</p>
                  <span className="ml-4 bg-red-100 text-red-800 text-sm font-semibold px-3 py-1 rounded-full">
                    Save {product.discount_percentage}%
                  </span>
                </div>
              ) : (
                <p className="text-3xl font-bold text-gray-800">${product.price}</p>
              )}
            </div>

            {deal && (
              <div className="mt-4 p-4 border-2 border-yellow-400 rounded-lg bg-yellow-50">
                <h2 className="text-lg font-bold text-yellow-800">{deal.title}</h2>
                <p className="text-yellow-700">{deal.description}</p>
                <p className="mt-2 text-sm text-yellow-600">
                  Valid until {new Date(deal.end_date).toLocaleDateString()}
                </p>
              </div>
            )}

            <div className="mt-6">
              <p className="text-gray-600">{product.description}</p>
            </div>

            <div className="mt-6">
              {!product.is_available || product.stock_quantity <= 0 ? (
                <p className="text-red-600 font-semibold">Out of stock</p>
              ) : product.stock_quantity < 10 ? (
                <p className="text-orange-600">Low stock: only {product.stock_quantity} left</p>
              ) : (
                <p className="text-green-600">In stock ({product.stock_quantity} available)</p>
              )}
            </div>

            {product.is_available && product.stock_quantity > 0 && (
              <div className="mt-6 flex items-end">
                <div className="mr-4">
                  <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 mb-1">
                    Quantity
                  </label>
                  <select
                    id="quantity"
                    name="quantity"
                    className="block w-20 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    value={quantity}
                    onChange={handleQuantityChange}
                  >
                    {[...Array(Math.min(10, product.stock_quantity))].map((_, i) => (
                      <option key={i + 1} value={i + 1}>
                        {i + 1}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={handleAddToCart}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg transition-colors"
                >
                  Add to Cart
                </button>
              </div>
            )}

            <div className="mt-8">
              <p className="text-sm text-gray-500">SKU: {product.sku}</p>
              {product.category_names && product.category_names.length > 0 && (
                <div className="mt-2">
                  <span className="text-sm text-gray-500">Categories: </span>
                  {product.category_names.map((cat, index) => (
                    <span key={index} className="text-sm text-gray-500">
                      {cat}{index < product.category_names.length - 1 ? ', ' : ''}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {related_products && related_products.length > 0 && (
        <div className="mt-12">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Related Products</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {related_products.map((relatedProduct) => (
              <Link key={relatedProduct.id} to={`/product/${relatedProduct.id}`}></Link>
                <div className="bg-white shadow-md rounded-lg overflow-hidden h-full hover:shadow-lg transition-shadow">
                  {relatedProduct.image_url ? (
                    <img src={relatedProduct.image_url} alt={relatedProduct.name} className="w-full h-48 object-cover" />
                  ) : (
                    <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
                      <span className="text-gray-400">No image</span>
                    </div>
                  )}
                  
                  <div className="p-4">
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">{relatedProduct.name}</h3>
                    
                    <div className="flex justify-between items-center"></div>
                      {relatedProduct.discount_percentage > 0 ? (
                        <div>
                          <p className="text-gray-400 line-through">${relatedProduct.price}</p>
                          <p className="text-xl font-bold text-green-600">${relatedProduct.discounted_price}</p>
                        </div>
                      ) : (
                        <p className="text-xl font-bold text-gray-800">${relatedProduct.price}</p>
                      )}
                    </div>
                    
                    {!relatedProduct.is_available || relatedProduct.stock_quantity <= 0 ? (
                      <p className="mt-2 text-red-600 text-sm">Out of stock</p>
                    ) : (
                      <p className="mt-2 text-green-600 text-sm">In stock</p>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductDetail;
