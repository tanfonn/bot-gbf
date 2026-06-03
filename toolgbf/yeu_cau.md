BẢN YÊU CẦU PHẦN MỀM: AUTO FARM BOT RPA (BẢN CẬP NHẬT)
1. Nền tảng và Mục đích cốt lõi
Loại ứng dụng: Ứng dụng chạy trên máy tính (Desktop App) có giao diện đồ họa (GUI).

Mục tiêu: Tự động hóa các thao tác chơi game (Auto Farm) cho một trò chơi chạy trên trình duyệt Google Chrome.

2. Cơ chế nhận diện hình ảnh thông minh
Khoanh vùng hoạt động (ROI): Cho phép người dùng kéo thả một khung hình chữ nhật lớn trên màn hình để giới hạn phạm vi bot quét tìm ảnh, giúp tối ưu hóa CPU.

Cắt ảnh mẫu trực tiếp (Dynamic Capture): Người dùng có thể dùng chuột kéo khung chữ nhật nhỏ bao quanh bất kỳ nút bấm nào trong game để tool tự động chụp, trích xuất hình dạng và lưu lại làm mẫu nhận diện (Template). Không cần chụp và cắt ảnh thủ công bằng phần mềm bên ngoài.

Đợi linh hoạt (Dynamic Wait): Bot có khả năng điều chỉnh thời gian chờ linh động, liên tục quét và chỉ thực hiện click khi nút mục tiêu thực sự xuất hiện trên màn hình ứng dụng.

Nhận diện chính xác: Sử dụng thuật toán xử lý ảnh (Computer Vision) để khớp ảnh mẫu với độ chính xác cao kể cả khi có sự thay đổi nhẹ về màu sắc, ánh sáng trong game.

3. Cơ chế chạy ngầm không chiếm chuột (Background Control) [MỚI BỔ SUNG]
Chụp ảnh ngầm: Thay vì chụp toàn bộ màn hình hiển thị, tool sẽ tự động tìm mã định danh cửa sổ (Window Handle) của Chrome để chụp lại hình ảnh của riêng luồng ứng dụng đó, ngay cả khi cửa sổ Chrome bị che khuất bởi ứng dụng khác.

Click không di chuột thật: Loại bỏ việc sử dụng con trỏ chuột vật lý của máy tính. Tool sẽ gửi trực tiếp các thông điệp click (tín hiệu tọa độ X, Y ngầm) thẳng vào cửa sổ Chrome thông qua API hệ điều hành.

Hiệu quả: Người dùng có thể vừa bật bot farm game ngầm, vừa di chuyển chuột thật để làm việc, lướt web, xem phim hoặc chơi một tựa game khác trên cùng một máy tính mà không bị gián đoạn.

4. Logic điều khiển và Kịch bản hành động
Chức năng 1 - Chạy tuần tự (Sequence): Dò và nhấn các nút lần lượt theo đúng chuỗi hành động được sắp xếp sẵn (Nút A click thành công mới chuyển sang dò nút B).

Chức năng 2 - Chạy định kỳ (Schedule): Thiết lập một hoặc nhiều nút bấm chạy độc lập theo thời gian (Hẹn giờ lặp lại sau mỗi X giây, ví dụ như tự động buff máu/skill). Chế độ này chạy ngầm song song và có quyền ưu tiên cao hơn để tạm ngắt chuỗi tuần tự khi đến giờ.

5. Quản lý cấu hình dữ liệu (Persistence)
Tự động lưu trữ: Toàn bộ tọa độ vùng quét (ROI), danh sách kịch bản, thời gian hẹn giờ và các file ảnh nút bấm cắt trực tiếp sẽ được lưu lại vĩnh viễn vào bộ nhớ máy tính (thư mục ảnh và file cấu hình .json).

Tái sử dụng: Khi tắt tool và mở lại vào lần sau, phần mềm tự động tải lại toàn bộ cấu hình cũ. Người dùng chỉ cần bấm nút Start để chạy ngay mà không cần thiết lập (setup) lại từ đầu.