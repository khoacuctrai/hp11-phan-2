Tính năng của hệ thống hiện tại
1. Đăng ký, đăng nhập, đăng xuất
Người dùng có thể đăng ký tài khoản (/signup/), gửi email chào mừng khi đăng ký thành công.

Người dùng có thể đăng nhập (/login/), gửi email thông báo đăng nhập thành công.

Có chức năng đăng xuất (/logout/).

2. Trang chủ và Carousel
Trang chủ (/) hiển thị sản phẩm nổi bật chia nhóm 3 sản phẩm/hàng.

Hiển thị ảnh carousel động.

3. Danh mục sản phẩm
Hiển thị sản phẩm theo từng danh mục:

iPhone (/iphone/)

MacBook (/macbook/)

iPad (/ipad/)

Watch (/watch/)

Tai nghe, loa (/audio/)

Phụ kiện (/accessory/)

4. Trang chi tiết sản phẩm
Trang chi tiết mỗi sản phẩm (/product/<id>/), hiển thị:

Thông tin sản phẩm, màu sắc, biến thể, bình luận, sản phẩm liên quan.

Thêm vào giỏ hàng (chọn biến thể nếu có).

5. Giỏ hàng
Xem danh sách sản phẩm đã thêm vào giỏ (/cart/).

Thêm vào giỏ hàng từ trang sản phẩm (/add-to-cart/<id>/).

Tăng/giảm/xoá số lượng từng mặt hàng trong giỏ:

Tăng: /cart/increase/<item_id>/

Giảm: /cart/decrease/<item_id>/

Xoá: /cart/remove/<item_id>/

6. Đặt hàng và thanh toán
Thanh toán từ giỏ hàng (/checkout/):

Tạo đơn hàng, lưu thông tin người nhận, email, địa chỉ...

Gửi email xác nhận đơn hàng cho khách.

Thanh toán QR (/cart/qr-payment/): sinh QR code chứa thông tin đơn hàng và xác nhận thanh toán.

Xem lịch sử đơn hàng của mình (/order-history/).

7. Bình luận và tương tác sản phẩm
Người dùng có thể bình luận trên trang sản phẩm.

Có thể like/dislike bình luận (/comment/<id>/<reaction_type>/).

8. Quản lý kho (Inventory Management)
Trang quản lý kho chỉ dành cho admin/staff (/inventory/):

Xem tất cả sản phẩm, số lượng tồn kho.

Chỉnh sửa tồn kho sản phẩm trực tiếp ngay trên web.

Đảm bảo chỉ admin/staff truy cập được.

9. Góp ý, khiếu nại
Trang gửi góp ý/khiếu nại dành cho user (/feedback/).

10. Tìm kiếm sản phẩm
Tìm kiếm sản phẩm theo tên (/search/?q=...).

11. Xử lý hình ảnh
Sản phẩm, biến thể, màu sắc đều hỗ trợ upload hình ảnh.

Carousel cũng có ảnh.

12. Quản trị bằng Django Admin
Các model đã khai báo có thể đăng ký vào trang admin để quản lý (theo hướng dẫn phía trên).

13. Quản lý Order, OrderItem
Khi đặt hàng, các item sẽ tạo OrderItem, lưu chi tiết số lượng, biến thể sản phẩm.

Có thể xem lại lịch sử đơn hàng.

Những điểm nổi bật/có thể nâng cấp
Đã gửi email cho các action quan trọng.

Đã phân quyền trang quản lý kho cho staff.

Dùng session cho giỏ hàng và quản lý chi tiết từng user.

Mỗi sản phẩm đều có quản lý tồn kho.

Tóm tắt tuyến tính năng cho từng url:
Đường dẫn	Tính năng
/	Trang chủ, carousel, sản phẩm nổi bật
/signup/	Đăng ký, gửi mail chào mừng
/login/	Đăng nhập, gửi mail thông báo
/logout/	Đăng xuất
/product/<id>/	Chi tiết sản phẩm, bình luận, thêm giỏ hàng
/add-to-cart/<id>/	Thêm sản phẩm vào giỏ
/cart/	Xem giỏ hàng
/cart/increase/<item_id>/, ...	Tăng/giảm/xoá giỏ hàng
/checkout/	Đặt hàng, email xác nhận
/cart/qr-payment/	Thanh toán QR
/order-history/	Lịch sử mua hàng
/feedback/	Gửi góp ý/khiếu nại
/inventory/	Quản lý kho (staff/admin)
/search/	Tìm kiếm sản phẩm
/iphone/, ...	Danh mục sản phẩm

Các tính năng chưa có (gợi ý phát triển)
Không có đăng ký/đổi mật khẩu bằng OTP/email xác thực.

Không có phân quyền admin/user nâng cao.

Chưa kiểm soát tồn kho ở mức variant (nếu cần).

Chưa có thống kê báo cáo đơn hàng/kho.

Chưa có quản lý khuyến mãi/giảm giá.

Nếu muốn chi tiết code của từng chức năng, hoặc muốn phát triển thêm tính năng nào, bạn chỉ cần nhắn rõ!
