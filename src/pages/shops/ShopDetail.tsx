import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Shop, Product, Deal, shopService } from '../api/shopService';

interface ShopPreviewData {
  shop: Shop;
  products: Product[];
  deals: Deal[];
}

const ShopDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [shopData, setShopData] = useState<ShopPreviewData | null>(null);

  useEffect(() => {
    const fetchShopData = async () => {
      try {
        setLoading(true);
        const data = await shopService.getShopPreview(Number(id));
        setShopData(data);
        setError(null);
      } catch (err) {
        setError('Failed to load shop details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchShopData();
    }
  }, [id]);

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading shop details...</div>;
  }

  if (error || !shopData) {
    return <div className="text-red-500 text-center">{error || 'Shop not found'}</div>;
  }

  const { shop, products, deals } = shopData;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white shadow-lg rounded-lg overflow-hidden">
        <div className="md:flex">
          {/* Shop Logo/Banner */}
          <div className="md:w-1/3 bg-gray-200">
            {shop.logo_url ? (
              <img src={shop.logo_url} alt={shop.name} className="w-full h-64 object-cover" />
            ) : (
              <div className="w-full h-64 flex items-center justify-center bg-gray-300">
                <span className="text-xl text-gray-500">No Image</span>
              </div>
            )}
          </div>

          {/* Shop Details */}
          <div className="md:w-2/3 p-6">
            <div className="flex justify-between items-start">
              <h1 className="text-3xl font-bold text-gray-800">{shop.name}</h1>
              {shop.is_verified && (
                <span className="bg-green-100 text-green-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                  Verified
                </span>
              )}
            </div>

            <div className="flex items-center mt-2">
              <div className="flex items-center">
                {[...Array(5)].map((_, i) => (
                  <svg
                    key={i}
                    className={`w-5 h-5 ${
                      i < Math.floor(shop.rating) ? 'text-yellow-400' : 'text-gray-300'
                    }`}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
                <span className="ml-2 text-gray-600">{shop.rating} / 5</span>
              </div>
              <span className="mx-4 text-gray-400">|</span>
              <div className="text-gray-600">{shop.deal_count} active deals</div>
            </div>

            <p className="mt-4 text-gray-600">{shop.description}</p>

            {shop.location_details && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold text-gray-700">Location</h3>
                <p className="text-gray-600">
                  {shop.location_details.address}, {shop.location_details.city}
                  <br />
                  {shop.location_details.state}, {shop.location_details.country}{' '}
                  {shop.location_details.postal_code}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Active Deals Section */}
      {deals && deals.length > 0 && (
        <div className="mt-10">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Current Deals</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {deals.map((deal) => (
              <div key={deal.id} className="bg-white shadow-md rounded-lg overflow-hidden border-2 border-yellow-400">
                <div className="p-5">
                  <div className="flex justify-between items-start">
                    <h3 className="text-xl font-bold text-gray-800">{deal.title}</h3>
                    {deal.is_featured && (
                      <span className="bg-yellow-100 text-yellow-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                        Featured
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-gray-600 h-20 overflow-hidden">{deal.description}</p>
                  
                  <div className="mt-4 flex justify-between items-center">
                    <div>
                      <p className="text-gray-400 line-through">${deal.original_price}</p>
                      <p className="text-2xl font-bold text-green-600">${deal.discounted_price}</p>
                    </div>
                    <div className="bg-red-100 text-red-800 text-sm font-semibold px-3 py-1 rounded-full">
                      Save {deal.discount_percentage}%
                    </div>
                  </div>

                  <p className="mt-3 text-sm text-gray-500">
                    Valid until {new Date(deal.end_date).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Products Section */}
      {products && products.length > 0 && (
        <div className="mt-10">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">Products</h2>
            <Link
              to={`/shop/${id}/products`}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              View All Products
            </Link>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {products.map((product) => (
              <Link key={product.id} to={`/product/${product.id}`}>
                <div className="bg-white shadow-md rounded-lg overflow-hidden h-full hover:shadow-lg transition-shadow">
                  {product.image_url ? (
                    <img src={product.image_url} alt={product.name} className="w-full h-48 object-cover" />
                  ) : (
                    <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
                      <span className="text-gray-400">No image</span>
                    </div>
                  )}
                  
                  <div className="p-4">
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">{product.name}</h3>
                    
                    <div className="flex justify-between items-center">
                      {product.discount_percentage > 0 ? (
                        <div>
                          <p className="text-gray-400 line-through">${product.price}</p>
                          <p className="text-xl font-bold text-green-600">${product.discounted_price}</p>
                        </div>
                      ) : (
                        <p className="text-xl font-bold text-gray-800">${product.price}</p>
                      )}
                      
                      {product.is_featured && (
                        <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                          Featured
                        </span>
                      )}
                    </div>
                    
                    {!product.is_available || product.stock_quantity <= 0 ? (
                      <p className="mt-2 text-red-600 text-sm">Out of stock</p>
                    ) : product.stock_quantity < 10 ? (
                      <p className="mt-2 text-orange-600 text-sm">Low stock: {product.stock_quantity} left</p>
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

export default ShopDetail;