# Triển khai online

**Muốn mở bằng đường link, không chạy Python trên máy?** Đọc **[DEPLOY-RENDER.md](DEPLOY-RENDER.md)**.

Gói đã có Blueprint `render.yaml`, Gunicorn và lớp mật khẩu/phiên/CSRF/giới hạn gọi API. Upload mã nguồn vào gốc repository, rồi Render → New → Blueprint. Mật khẩu tool chỉ đặt trong Render Environment; API Key nhập sau khi đăng nhập.

**Entry point online bắt buộc:** `gunicorn --config gunicorn.conf.py deploy_app:app`. Không dùng `app:app` cho website công khai vì đó là chế độ local không có đăng nhập. Gói mặc định dùng Free để thử nghiệm, không cam kết uptime hay khả năng chạy quy mô lớn. Chưa được triển khai vào tài khoản Render của bạn.

---

# LinkScope v1.1 — Giá bán, hoa hồng & lịch sử Shopee

Tool web để dán một cột link / Item ID hoặc nhập Excel, CSV; đọc giá và hoa hồng qua **AddLiveTag Product Data Batch API**, lọc, xuất Excel/CSV.

## Mở bằng nhấp đúp trên Windows (khuyến nghị)

Giải nén **toàn bộ** gói ZIP, rồi nhấp đúp **KHOI-DONG-LINKSCOPE.bat**.
File tự tìm Python 3.10+, tạo `.venv`, cài thư viện khi cần và mở trình duyệt sau khi server sẵn sàng. Nếu thiếu Python, mở trang tải Python chính thức để bạn cài, không tự cài phần mềm hệ thống. Các lần sau không cần gõ lệnh.

Giữ cửa sổ lệnh mở khi dùng, Ctrl+C để dừng. Nhấp đúp lần nữa khi đang chạy sẽ mở lại phiên server hiện tại. Cổng được chọn tự động để tránh xung đột; địa chỉ hiển thị trong cửa sổ lệnh. Chế độ này **chỉ bind 127.0.0.1**, không công khai server lên mạng.

Đây không phải EXE độc lập: vẫn cần Python và Internet để cài thư viện lần đầu / gọi API. Đọc `HUONG-DAN-MO-TOOL.txt` nếu cần hướng dẫn từng bước. Không chạy BAT trực tiếp từ trong ZIP. Không cần quyền quản trị hoặc tắt antivirus.

## Chạy bằng lệnh (tùy chọn)

Cần Python 3.10 trở lên. Mở terminal trong thư mục này:

```bash
python -m pip install -r requirements.txt
python app.py
```

Mở `http://localhost:8000`. Trên Windows có thể dùng `py` thay `python`, hoặc chạy `start-windows.bat`.

Máy phải có Internet để gọi API. UI không tải font, script hoặc thư viện từ CDN.

Server mặc định bind `0.0.0.0` để hỗ trợ bản xem trước. Chỉ chạy trong mạng đáng tin cậy; nếu chỉ dùng cá nhân trên máy, có thể đổi host trong app.py thành `127.0.0.1`. Bản này dùng Flask development server, không có tài khoản người dùng. Không đưa thẳng lên Internet cho nhiều người dùng: cần HTTPS, xác thực, rate limiting, giới hạn tài nguyên theo người dùng và WSGI server khi triển khai production.

## Sử dụng

1. Lấy key ở **https://addlivetag.com/tool/api-key.php → đăng nhập Google → Tạo Key**. Không gửi key trong chat hoặc commit vào mã nguồn.
2. Dán link đầy đủ / Item ID, hoặc chọn file `.xlsx` / `.csv` UTF-8. Excel đọc sheet đầu; chọn cột link và bỏ chọn tiêu đề nếu file không có header. Tối đa 10.000 dòng, 100 cột, file 12 MB.
3. “Rà soát link” không gọi API: tách ID, loại trùng và báo lỗi. Link rút gọn không hỗ trợ; mở link trên trình duyệt rồi copy link gốc.
4. Nhập key. Có thể tùy chỉnh tỷ lệ HH sàn (%) và trần HH theo tài khoản. Để trống để dùng mặc định của API. Nhập 3.5 nghĩa là 3,5%.
5. “Kiểm tra sản phẩm”: tool gọi batch. Chế độ thường 20 sản phẩm/lô, chờ ít nhất 15 giây sau lô trước; cache-only 100 sản phẩm/lô, chờ 4 giây. Tôn trọng cooldown và HTTP 429 (tối đa 2 lần thử lại cho 429). Lô còn lại không gửi khi nguồn lỗi nghiêm trọng.
6. Dừng: không gửi lô kế tiếp; yêu cầu đang chạy vẫn hoàn tất. Không đóng tab khi đang chạy.
7. Lọc giá / tổng % / tiền HH, sắp xếp. Xuất Excel/CSV **toàn bộ kết quả khớp bộ lọc**, không chỉ trang đang xem.
8. “Thử lại mục cần kiểm tra” chỉ gửi lại pending, stale, skipped, error, incomplete. Không tự gọi lại not_found.

## Định nghĩa dữ liệu

- Giá = trường `price` của API, không cam kết đúng giá sau voucher / mọi biến thể.
- HH sàn/Xtra = `shopeeRatePercent` / `sellerRatePercent`, nếu thiếu dùng `shopeeRate` / `sellerRate` × 100.
- Tổng HH = `totalRatePercent`, nếu thiếu chỉ cộng khi **cả hai** tỷ lệ thành phần đều có.
- Không suy tỷ lệ công bố từ `commission / price`. Tỷ lệ này được ghi riêng trong chi tiết và file xuất.
- Tiền HH = `commission` do API trả. Có thể đã áp dụng trần, user rate và thuế theo tài liệu; không phải cam kết thực nhận.
- Không dùng 0 để thay dữ liệu thiếu. Fallback không được coi là giá/hoa hồng đã xác minh. `commission_unverified` ẩn tỷ lệ và tiền HH.
- Dữ liệu cũ có nhãn riêng; có thể loại khỏi kết quả bằng “Chỉ hiện dữ liệu đầy đủ, không cũ”.
- Cache theo tài liệu khoảng 3 giờ, có thể lâu hơn nếu API nguồn lỗi.
- Nút “Xem bản mẫu” chỉ tạo dữ liệu giả lập để xem UI. Không gọi API; file xuất được đánh dấu DEMO.

## Quyền riêng tư & an toàn

- Key nhập trong ô password, gửi trong body đến backend rồi trong header `X-API-Key` đến endpoint cố định của AddLiveTag. Không dùng query string, file cấu hình, localStorage, cookie hay log để lưu key.
- Key vẫn nằm trong bộ nhớ trang cho đến khi xóa/tải lại. Danh sách và kết quả không lưu bền vững; hãy xuất trước khi đóng tab.
- File upload được xử lý trong bộ nhớ server, không ghi vào file. Danh sách ID được gửi cho AddLiveTag khi kiểm tra. Không bảo đảm cách nhà cung cấp API lưu/xử lý dữ liệu.
- URL nhập không được fetch tự do: chỉ trích ID từ host Shopee VN cho phép. Không có tính năng bung link rút gọn.
- Dữ liệu hiển thị được escape; xuất bảng có chặn công thức bắt đầu bằng `=`, `+`, `-`, `@` trong chuỗi.

## API và phạm vi

Endpoint: `https://data.addlivetag.com/product-data/product-data-batch.php`

Nguồn tài liệu:
- https://unikorn.vn/p/shopee-product-data-api
- https://github.com/bcat95/shopee-aff/blob/main/product-data-api.md
- https://github.com/bcat95/shopee-aff/blob/main/docs/product-data-batch.md

API được chia sẻ công khai nhưng yêu cầu key từ **01/10/2026**. Đây là API bên thứ ba trên AddLiveTag, không phải endpoint trực tiếp của Shopee. Tài liệu giới hạn học tập, nghiên cứu và nội bộ phi thương mại; tự kiểm chứng dữ liệu trước khi sử dụng.

Tài liệu có số hạn mức nguồn không thống nhất ở phần tóm tắt và phần thân. Tool dùng nhịp bảo thủ và tôn trọng tín hiệu giới hạn thực tế thay vì cam kết một quota cố định.

## Kiểm thử

```bash
python -m pip install pytest
python -m pytest -q
```

Unit test dùng phản hồi giả lập cho provider: phân tích URL, loại trùng, dữ liệu thiếu/0, map sản phẩm theo ID, chuyển tỷ lệ %, xử lý 429, import CSV/XLSX và export chống formula injection.

**Chưa kiểm chứng dữ liệu thật bằng key của người dùng.** Cần chạy vài link thật với key hợp lệ để xác nhận tài khoản/quota và phản hồi live. Các kiểm thử giả lập không thay thế bước này.


## v1.1 — Tích hợp đúng 2 API admin hướng dẫn

1. **Product Data Batch**: giá bán, % HH sàn, % HH Xtra, tổng HH, tiền HH, tổng đã bán (`sales`, lịch sử tích lũy) và đánh giá.
2. **Price & Commission History**: `https://data.addlivetag.com/price-tracking/history.php`, gửi `type=both`, `changes_only=1`, `no_product=1`; không gọi API nguồn Shopee. Vẫn cần API Key hợp lệ.

### Cách dùng phần mới

- Link lấy key chính xác: https://addlivetag.com/tool/api-key.php (chuyển đến đăng nhập Google nếu chưa có phiên).
- Mặc định bật **Kèm lịch sử giá & HH**. Sau khi kiểm tra dữ liệu hiện tại, tool tải thêm lịch sử. Có thể bỏ chọn để chỉ lấy dữ liệu hiện tại.
- Lịch sử nhận tối đa 50 ID/lô, giãn 6 giây giữa lô (tài liệu: 600 sản phẩm/phút theo IP). Dừng không hủy lô đang chạy. HTTP 429 thử lại tối đa 2 lần, tôn trọng Retry-After tối thiểu 60 giây.
- Tối đa 500 sản phẩm mỗi thao tác tải lịch sử. Nếu danh sách lớn hơn, lọc rồi dùng **Tải danh sách đã lọc**, hoặc **Tải SP này**.
- Chọn khoảng 30 / 90 / 180 / 365 / 730 ngày. Khi đổi khoảng hoặc cấu hình tier, cần bấm tải lại; không tự gọi API chỉ vì đổi dropdown.
- Bấm biểu tượng đồng hồ cạnh sản phẩm để chọn lịch sử trong panel. Biểu đồ bậc thang phản ánh dữ liệu theo ngày, không giả định trước điểm đầu; các điểm thiếu không nối qua. Nếu dữ liệu bị cắt, không kéo dài mức cuối tới cuối khoảng.
- Bảng mốc giá và mốc HH phân trang, mới nhất trước. Giữ nguyên và đánh dấu điểm `suspect`, không tự sửa số.
- **Xuất Excel lịch sử**: xuất các lịch sử đã tải của sản phẩm khớp bộ lọc, gồm sheet tổng quan/cảnh báo/cấu hình, giá, hoa hồng và lưu ý. Xuất tối đa 500 sản phẩm, 100.000 điểm mỗi file. File hiện tại và file lịch sử là hai nút xuất riêng.
- Bảng chính có cột/lọc/sắp xếp **Tổng đã bán**, file Excel/CSV chính có thêm tổng đã bán và đánh giá. Không suy ra lượt bán theo ngày từ hai API này.

### Cảnh báo quan trọng về lịch sử hoa hồng

Theo tài liệu, HH sàn trong lịch sử ghi theo tài khoản đã thu thập dữ liệu từng ngày. Việc đổi tài khoản thu thập có thể tạo biến động giả. Hãy điền cả **HH sàn theo tài khoản (%)** và **Trần HH sàn** đúng tài khoản của bạn. Tool không tự đặt tier cho bạn.

Tool chỉ đánh dấu chuẩn hóa khi phản hồi API có `normalized: true` ở cấp được hỗ trợ. Nếu thiếu cấu hình hoặc thiếu xác nhận chuẩn hóa, vẫn hiện dữ liệu cùng cảnh báo rõ ràng; không khẳng định đó là HH đúng tài khoản. `suspect` và `limits.truncated` luôn được giữ trong bảng/cảnh báo/file. Các số gốc trong `recorded` được đưa vào file lịch sử nếu nguồn cung cấp.

API lịch sử chỉ có độ phân giải NGÀY (bản ghi cuối ngày). `stats` tính theo toàn bộ ngày trong khoảng, không chỉ các mốc thay đổi đang vẽ. `no_data` nghĩa là kho chưa có lịch sử trong khoảng, không phải giá/HH bằng 0. Lỗi lịch sử không xóa kết quả giá/HH hiện tại.

Tài liệu: https://data.addlivetag.com/#price-commission-history và https://data.addlivetag.com/shopee/

### Kiểm thử bổ sung

Có test phản hồi giả lập cho 2 API: map ID, tier, giữ số 0, không tính % từ tiền, no_data, suspect, dữ liệu bị cắt, 401/403/429/5xx, export XLSX nhiều sheet và chống công thức. Đã kiểm thử UI bản mẫu, bộ lọc đã bán, chọn sản phẩm, biểu đồ, cảnh báo, xuất file và màn hình di động. **Chưa xác minh dữ liệu thật bằng API Key của người dùng.**
