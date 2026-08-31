import random
import numpy as np
from datetime import datetime, timedelta

# Product Catalog
PRODUCT_CATEGORIES = ["Electronics", "Apparel", "Home", "Beauty", "Sports"]
PRODUCTS = []
for i in range(200):
    category = PRODUCT_CATEGORIES[i % len(PRODUCT_CATEGORIES)]
    # Use log-normal distribution for prices: Electronics are more expensive
    if category == "Electronics":
        base_price = float(np.random.lognormal(5.0, 0.5))
    elif category == "Apparel":
        base_price = float(np.random.lognormal(3.5, 0.4))
    elif category == "Home":
        base_price = float(np.random.lognormal(4.0, 0.4))
    elif category == "Beauty":
        base_price = float(np.random.lognormal(3.0, 0.3))
    else:
        base_price = float(np.random.lognormal(3.8, 0.4))
    
    # Clip price to reasonable range
    price = max(5.00, min(1500.00, round(base_price, 2)))
    PRODUCTS.append({
        "product_id": f"PROD_{i:03d}",
        "category": category,
        "price": price
    })

# Location Pool
US_STATES = ["NY", "CA", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI", "WA", "AZ", "CO", "VA", "MA"]
CITIES = {
    "NY": ["New York", "Buffalo", "Rochester"],
    "CA": ["Los Angeles", "San Francisco", "San Diego", "San Jose"],
    "TX": ["Houston", "Austin", "Dallas", "San Antonio"],
    "FL": ["Miami", "Orlando", "Tampa", "Jacksonville"],
    "IL": ["Chicago", "Springfield"],
    "PA": ["Philadelphia", "Pittsburgh"],
    "OH": ["Columbus", "Cleveland", "Cincinnati"],
    "GA": ["Atlanta", "Savannah"],
    "NC": ["Charlotte", "Raleigh"],
    "MI": ["Detroit", "Grand Rapids"],
    "WA": ["Seattle", "Tacoma"],
    "AZ": ["Phoenix", "Tucson"],
    "CO": ["Denver", "Colorado Springs"],
    "VA": ["Richmond", "Virginia Beach"],
    "MA": ["Boston", "Worcester"]
}

LOCATION_POOL = []
for state, cities in CITIES.items():
    for city in cities:
        LOCATION_POOL.append(f"{city}, {state}")

PAYMENT_METHODS = ["Credit Card", "PayPal", "Apple Pay", "Google Pay", "Bank Transfer"]

def get_random_location():
    return random.choice(LOCATION_POOL)

def get_random_payment_method():
    # Credit Card and PayPal are most common
    weights = [0.55, 0.25, 0.10, 0.08, 0.02]
    return random.choices(PAYMENT_METHODS, weights=weights)[0]

def generate_coupons(start_time, total_seconds):
    """Generate 50 coupons with varying campaigns and validity periods."""
    coupons = []
    # Coupon 0 to 49
    for i in range(50):
        coupon_id = f"COUPON_{i:02d}"
        discount = random.choice([10, 15, 20, 25, 30, 50])
        campaign_id = f"CAMP_{i // 5:02d}"  # 10 campaigns in total
        
        # Decide validity duration
        valid_duration_days = random.choice([30, 60, 90, 365])
        # Random start day within the year
        start_offset_days = random.randint(0, 365 - valid_duration_days)
        
        valid_from = start_time + timedelta(days=start_offset_days)
        valid_until = valid_from + timedelta(days=valid_duration_days)
        
        coupons.append({
            "coupon_id": coupon_id,
            "discount_percentage": discount,
            "campaign_id": campaign_id,
            "valid_from": valid_from.strftime("%Y-%m-%d %H:%M:%S"),
            "valid_until": valid_until.strftime("%Y-%m-%d %H:%M:%S")
        })
    return coupons

def generate_device_and_ip_pools():
    """Pre-generate pools of unique devices and IPs."""
    devices = [f"D{i:05d}" for i in range(35000)]
    ips = []
    for _ in range(40000):
        ips.append(f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(1, 254)}")
    
    # Assign a default location to each device and IP to ensure spatial consistency when shared
    device_locs = {d: get_random_location() for d in devices}
    ip_locs = {ip: get_random_location() for ip in ips}
    
    return devices, ips, device_locs, ip_locs

def generate_legitimate_customers(num_customers, start_time, total_seconds, devices, ips, device_locs, ip_locs, coupons):
    """Generate legitimate customers, their transactions, and setup capacity for referrals."""
    customers = []
    
    # Pre-allocate devices and IPs to guarantee high uniqueness rates
    # 28,000 customers will get a unique device (chosen from the first 28,000 devices)
    # The remaining 18,000 customers will share devices from devices[30000:35000] (size 5,000)
    # For IPs: 32,000 unique IPs from ips[:32000], others share from ips[35000:40000] (size 5,000)
    
    unique_devices = devices[:28000].copy()
    random.shuffle(unique_devices)
    shared_device_pool = devices[30000:35000]
    
    unique_ips = ips[:32000].copy()
    random.shuffle(unique_ips)
    shared_ip_pool = ips[35000:40000]
    
    for i in range(num_customers):
        customer_id = f"C_{i:05d}"
        
        # Uniformly distribute registration across the year
        reg_offset = random.randint(0, total_seconds)
        reg_time = start_time + timedelta(seconds=reg_offset)
        
        # Device assignment
        if i < 28000:
            device_id = unique_devices[i]
        else:
            device_id = random.choice(shared_device_pool)
            
        # IP assignment
        if i < 32000:
            ip_address = unique_ips[i]
        else:
            ip_address = random.choice(shared_ip_pool)
            
        # Use location associated with device (or fall back to IP, or random)
        location = device_locs.get(device_id, ip_locs.get(ip_address, get_random_location()))
        
        # Assign referral capacity
        cap_roll = random.random()
        if cap_roll < 0.45:
            ref_capacity = 0
        elif cap_roll < 0.75:
            ref_capacity = 1
        elif cap_roll < 0.92:
            ref_capacity = 2
        elif cap_roll < 0.97:
            ref_capacity = 5
        else:
            ref_capacity = 10
            
        customers.append({
            "customer_id": customer_id,
            "account_created_at": reg_time,
            "location": location,
            "device_id": device_id,
            "ip_address": ip_address,
            "ref_capacity": ref_capacity,
            "is_abuse": False,
            "ring_id": None,
            "abuse_type": None
        })
        
    return customers

def generate_legitimate_referrals(customers, p_referred=0.60):
    """Generate realistic hierarchical referrals for legitimate customers.
    Ensure referrer registered before referred customer."""
    referrals = []
    
    # Sort customers by registration time to ensure chronological correctness
    sorted_customers = sorted(customers, key=lambda x: x["account_created_at"])
    
    # Active referrers list: list of customers registered so far who have capacity > 0
    active_referrers = []
    
    # The first customer cannot be referred
    if sorted_customers[0]["ref_capacity"] > 0:
        active_referrers.append(sorted_customers[0])
        
    for cust in sorted_customers[1:]:
        # Determine if this customer is referred
        if random.random() < p_referred and active_referrers:
            # Select a referrer
            referrer = random.choice(active_referrers)
            
            # Create referral (referral timestamp = referee's account creation time)
            referrals.append({
                "referrer_id": referrer["customer_id"],
                "referred_id": cust["customer_id"],
                "timestamp": cust["account_created_at"].strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Update capacity
            referrer["ref_capacity"] -= 1
            if referrer["ref_capacity"] <= 0:
                active_referrers.remove(referrer)
                
        # Add this customer to the potential referrers pool if they have capacity
        if cust["ref_capacity"] > 0:
            active_referrers.append(cust)
            
    return referrals

def generate_customer_transactions(customer, coupons, start_time, total_seconds):
    """Generate transactions for a single customer longitudinally."""
    transactions = []
    cust_id = customer["customer_id"]
    reg_time = customer["account_created_at"]
    
    # Poisson-distributed number of transactions: increase average to offset truncation
    num_tx = 1 + np.random.poisson(6.8)
    
    curr_time = reg_time
    for _ in range(num_tx):
        # Time gap between transactions: exponential distribution with mean of 15 days
        gap_seconds = int(np.random.exponential(15 * 24 * 3600))
        curr_time += timedelta(seconds=gap_seconds)
        
        # Stop if we exceed the end of the 1-year timeline
        end_time = start_time + timedelta(seconds=total_seconds)
        if curr_time >= end_time:
            break
            
        # Choose a product randomly
        product = random.choice(PRODUCTS)
        price = product["price"]
        
        # Coupon application: 20% probability
        coupon_applied = None
        amount = price
        if random.random() < 0.20:
            # Filter coupons valid at this transaction timestamp
            valid_coupons = [
                c for c in coupons 
                if datetime.strptime(c["valid_from"], "%Y-%m-%d %H:%M:%S") <= curr_time <= datetime.strptime(c["valid_until"], "%Y-%m-%d %H:%M:%S")
            ]
            if valid_coupons:
                coupon_applied = random.choice(valid_coupons)
                discount = coupon_applied["discount_percentage"]
                amount = round(price * (1 - discount / 100.0), 2)
                
        transactions.append({
            "transaction_id": None,  # Will be assigned globally
            "customer_id": cust_id,
            "amount": amount,
            "timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
            "coupon_id": coupon_applied["coupon_id"] if coupon_applied else None,
            "product_id": product["product_id"],
            "payment_method": get_random_payment_method()
        })
        
    return transactions

def generate_abuse_rings(num_rings, start_idx, target_total_fraud, start_time, total_seconds, devices, ips, device_locs, ip_locs, coupons):
    """Generate 100-150 abuse rings with different styles of coordination and split allocation."""
    rings_customers = []
    rings_transactions = []
    rings_referrals = []
    
    unique_fraud_devices = devices[28000:30000]
    unique_fraud_ips = ips[32000:35000]
    fraud_device_idx = 0
    fraud_ip_idx = 0
    
    # Calculate ring sizes to sum to target_total_fraud (~4000)
    # Average size around 33. S_i in [15, 50]
    sizes = []
    while sum(sizes) < target_total_fraud:
        sizes.append(random.randint(15, 50))
    # Adjust last size
    sizes[-1] = max(10, target_total_fraud - sum(sizes[:-1]))
    
    # Limit rings count if sizes exceeded or fell short
    num_rings = len(sizes)
    
    # Distribute rings to train (70%), val (15%), test (15%)
    splits = []
    for i in range(num_rings):
        roll = random.random()
        if roll < 0.70:
            splits.append("train")
        elif roll < 0.85:
            splits.append("val")
        else:
            splits.append("test")
            
    # Time window cutoffs
    t1_seconds = int(0.70 * total_seconds)
    t2_seconds = int(0.85 * total_seconds)
    
    current_fraud_id = start_idx
    
    abuse_types = ["referral_ring", "coupon_exploitation", "temporal_coordination", "similar_purchasing", "distributed_coordination", "mixed"]
    
    for r_idx, size in enumerate(sizes):
        ring_id = f"R{r_idx+1:03d}"
        abuse_type = abuse_types[r_idx % len(abuse_types)]
        split = splits[r_idx]
        
        # Establish temporal bounds for this ring based on its split
        if split == "train":
            s_min, s_max = 0, t1_seconds
        elif split == "val":
            s_min, s_max = t1_seconds, t2_seconds
        else:
            s_min, s_max = t2_seconds, total_seconds
            
        # The ring active duration is between 5 and 15 days
        duration_seconds = random.randint(5 * 24 * 3600, 15 * 24 * 3600)
        # Ensure we don't go outside the split bounds
        max_start = max(s_min, s_max - duration_seconds)
        if max_start == s_min:
            start_offset = s_min
        else:
            start_offset = random.randint(s_min, max_start)
            
        ring_start_time = start_time + timedelta(seconds=start_offset)
        ring_end_time = ring_start_time + timedelta(seconds=duration_seconds)
        
        # Generate ring members
        ring_members = []
        for m_idx in range(size):
            cust_id = f"C_{current_fraud_id:05d}"
            current_fraud_id += 1
            
            # Account created within the first 20% of the active window
            creation_seconds = random.randint(0, int(0.20 * duration_seconds))
            m_reg_time = ring_start_time + timedelta(seconds=creation_seconds)
            
            ring_members.append({
                "customer_id": cust_id,
                "account_created_at": m_reg_time,
                "is_abuse": True,
                "ring_id": ring_id,
                "abuse_type": abuse_type,
                "split": split  # Kept internally for tracking if needed
            })
            
        # Sort ring members chronologically by registration time to ensure valid referral hierarchies
        ring_members.sort(key=lambda x: x["account_created_at"])
            
        # Allocate device_id, ip_address, and location based on abuse pattern
        # Standard pools (mostly unique): first 30,000 devices, first 35,000 IPs
        # Shared pools: last 5,000 devices, last 5,000 IPs
        if abuse_type == "distributed_coordination":
            # No device or IP sharing, different locations
            for member in ring_members:
                member["device_id"] = unique_fraud_devices[fraud_device_idx]
                fraud_device_idx = (fraud_device_idx + 1) % len(unique_fraud_devices)
                
                member["ip_address"] = unique_fraud_ips[fraud_ip_idx]
                fraud_ip_idx = (fraud_ip_idx + 1) % len(unique_fraud_ips)
                
                member["location"] = device_locs[member["device_id"]]
        elif abuse_type in ["coupon_exploitation", "mixed"]:
            # Heavy sharing: 2-3 devices and IPs for the whole ring
            shared_k = random.randint(2, 3)
            ring_devices = [random.choice(devices[30000:]) for _ in range(shared_k)]
            ring_ips = [random.choice(ips[35000:]) for _ in range(shared_k)]
            for member in ring_members:
                member["device_id"] = random.choice(ring_devices)
                member["ip_address"] = random.choice(ring_ips)
                # Location matches device
                member["location"] = device_locs[member["device_id"]]
        else:
            # Moderate sharing: S // 4 devices and IPs
            shared_k = max(2, size // 4)
            ring_devices = [random.choice(devices[30000:]) for _ in range(shared_k)]
            ring_ips = [random.choice(ips[35000:]) for _ in range(shared_k)]
            for member in ring_members:
                # 60% probability to share, 40% probability to get unique device
                if random.random() < 0.60:
                    member["device_id"] = random.choice(ring_devices)
                else:
                    member["device_id"] = unique_fraud_devices[fraud_device_idx]
                    fraud_device_idx = (fraud_device_idx + 1) % len(unique_fraud_devices)
                    
                if random.random() < 0.60:
                    member["ip_address"] = random.choice(ring_ips)
                else:
                    member["ip_address"] = unique_fraud_ips[fraud_ip_idx]
                    fraud_ip_idx = (fraud_ip_idx + 1) % len(unique_fraud_ips)
                    
                member["location"] = device_locs[member["device_id"]]
                
        # Append customers to master list
        for m in ring_members:
            rings_customers.append({
                "customer_id": m["customer_id"],
                "account_created_at": m["account_created_at"],
                "location": m["location"],
                "device_id": m["device_id"],
                "ip_address": m["ip_address"],
                "is_abuse": True,
                "ring_id": ring_id,
                "abuse_type": abuse_type,
                "split": m["split"]
            })
            
        # Generate referrals for this ring
        if abuse_type in ["referral_ring", "mixed", "distributed_coordination"]:
            # Dense referral structure: e.g. star (70%) or dense DAG (30%)
            if random.random() < 0.70:
                # Star: First member (leader) refers everyone else
                leader = ring_members[0]
                for follower in ring_members[1:]:
                    # Check chronological ordering: referee must be created at or after referrer
                    ref_time = follower["account_created_at"]
                    # If referee registers at the same time or after leader, it works
                    if ref_time < leader["account_created_at"]:
                        ref_time = leader["account_created_at"]
                    rings_referrals.append({
                        "referrer_id": leader["customer_id"],
                        "referred_id": follower["customer_id"],
                        "timestamp": ref_time.strftime("%Y-%m-%d %H:%M:%S")
                    })
            else:
                # Dense DAG: Members refer others registered before them
                # Sort members by registration time
                sorted_members = sorted(ring_members, key=lambda x: x["account_created_at"])
                for i in range(1, len(sorted_members)):
                    # Each member is referred by someone earlier in the ring with 90% probability
                    if random.random() < 0.90:
                        ref_idx = random.randint(0, i - 1)
                        referrer = sorted_members[ref_idx]
                        referee = sorted_members[i]
                        rings_referrals.append({
                            "referrer_id": referrer["customer_id"],
                            "referred_id": referee["customer_id"],
                            "timestamp": referee["account_created_at"].strftime("%Y-%m-%d %H:%M:%S")
                        })
        else:
            # Sparse referrals within the ring (similar to normal referrals but only within ring members)
            sorted_members = sorted(ring_members, key=lambda x: x["account_created_at"])
            for i in range(1, len(sorted_members)):
                if random.random() < 0.30:  # 30% referral rate
                    ref_idx = random.randint(0, i - 1)
                    referrer = sorted_members[ref_idx]
                    referee = sorted_members[i]
                    rings_referrals.append({
                        "referrer_id": referrer["customer_id"],
                        "referred_id": referee["customer_id"],
                        "timestamp": referee["account_created_at"].strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
        # Generate transactions for this ring
        # Find valid coupons for this ring's time range
        ring_valid_coupons = []
        for c in coupons:
            c_start = datetime.strptime(c["valid_from"], "%Y-%m-%d %H:%M:%S")
            c_end = datetime.strptime(c["valid_until"], "%Y-%m-%d %H:%M:%S")
            # Overlaps if coupon is valid for the ENTIRE duration of the ring
            if c_start <= ring_start_time and c_end >= ring_end_time:
                ring_valid_coupons.append(c)
                
        # If no coupon covers the entire range, fall back to any coupon that overlaps at all
        if not ring_valid_coupons:
            for c in coupons:
                c_start = datetime.strptime(c["valid_from"], "%Y-%m-%d %H:%M:%S")
                c_end = datetime.strptime(c["valid_until"], "%Y-%m-%d %H:%M:%S")
                if c_start <= ring_end_time and c_end >= ring_start_time:
                    ring_valid_coupons.append(c)
            # If still none, fall back to any coupon
            if not ring_valid_coupons:
                ring_valid_coupons = coupons
            
        ring_coupon = random.choice(ring_valid_coupons)
        
        # Product and payment method coordination for Similar Purchasing
        coor_product = random.choice(PRODUCTS)
        coor_payment = get_random_payment_method()
        
        if abuse_type in ["temporal_coordination", "mixed"]:
            # Coordinated in time: transactions occur in tight bursts
            # 3 bursts within the ring's active duration
            num_bursts = 3
            burst_offsets = sorted([random.randint(int(0.20 * duration_seconds), duration_seconds - 60) for _ in range(num_bursts)])
            
            for offset in burst_offsets:
                burst_center = ring_start_time + timedelta(seconds=offset)
                # 80-100% of members participate in each burst
                participants = random.sample(ring_members, k=int(random.uniform(0.8, 1.0) * size))
                
                for member in participants:
                    # Transaction is within 60 seconds of the burst center
                    t_offset = random.randint(-30, 30)
                    tx_time = burst_center + timedelta(seconds=t_offset)
                    
                    # Ensure transaction happens after member registered
                    if tx_time < member["account_created_at"]:
                        tx_time = member["account_created_at"] + timedelta(seconds=random.randint(1, 10))
                        
                    # Product and amount
                    if abuse_type == "mixed":
                        # Mix: identical products, payments, and coupons
                        product = coor_product
                        payment_method = coor_payment
                        coupon_applied = ring_coupon
                    else:
                        product = random.choice(PRODUCTS)
                        payment_method = get_random_payment_method()
                        # Normal coupon use probability
                        coupon_applied = ring_coupon if random.random() < 0.20 else None
                        
                    # Clip to coupon validity if one is applied
                    if coupon_applied:
                        cp_start = datetime.strptime(coupon_applied["valid_from"], "%Y-%m-%d %H:%M:%S")
                        cp_end = datetime.strptime(coupon_applied["valid_until"], "%Y-%m-%d %H:%M:%S")
                        if tx_time < cp_start:
                            tx_time = cp_start + timedelta(seconds=random.randint(1, 60))
                        elif tx_time > cp_end:
                            tx_time = cp_end - timedelta(seconds=random.randint(1, 60))
                        
                    price = product["price"]
                    amount = price
                    if coupon_applied:
                        discount = coupon_applied["discount_percentage"]
                        amount = round(price * (1 - discount / 100.0), 2)
                        
                    rings_transactions.append({
                        "transaction_id": None,
                        "customer_id": member["customer_id"],
                        "amount": amount,
                        "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "coupon_id": coupon_applied["coupon_id"] if coupon_applied else None,
                        "product_id": product["product_id"],
                        "payment_method": payment_method
                    })
        else:
            # Distributed in time, but coordinated in attributes
            for member in ring_members:
                # 3 to 6 transactions per member
                num_tx = random.randint(3, 6)
                m_reg_time = member["account_created_at"]
                
                for tx_i in range(num_tx):
                    # Distribute transactions uniformly in the remaining active duration
                    rem_duration = int((ring_end_time - m_reg_time).total_seconds())
                    if rem_duration <= 0:
                        tx_time = m_reg_time + timedelta(seconds=10)
                    else:
                        tx_offset = random.randint(1, rem_duration)
                        tx_time = m_reg_time + timedelta(seconds=tx_offset)
                        
                    # Coupon exploitation ring forces same coupon code
                    if abuse_type == "coupon_exploitation":
                        coupon_applied = ring_coupon
                        product = random.choice(PRODUCTS)
                        payment_method = get_random_payment_method()
                    # Similar purchasing ring forces same product and payment
                    elif abuse_type == "similar_purchasing":
                        coupon_applied = ring_coupon if random.random() < 0.20 else None
                        product = coor_product
                        payment_method = coor_payment
                    else:
                        coupon_applied = ring_coupon if random.random() < 0.20 else None
                        product = random.choice(PRODUCTS)
                        payment_method = get_random_payment_method()
                        
                    # Clip to coupon validity if one is applied
                    if coupon_applied:
                        cp_start = datetime.strptime(coupon_applied["valid_from"], "%Y-%m-%d %H:%M:%S")
                        cp_end = datetime.strptime(coupon_applied["valid_until"], "%Y-%m-%d %H:%M:%S")
                        if tx_time < cp_start:
                            tx_time = cp_start + timedelta(seconds=random.randint(1, 60))
                        elif tx_time > cp_end:
                            tx_time = cp_end - timedelta(seconds=random.randint(1, 60))
                        
                    price = product["price"]
                    amount = price
                    if coupon_applied:
                        discount = coupon_applied["discount_percentage"]
                        amount = round(price * (1 - discount / 100.0), 2)
                        
                    rings_transactions.append({
                        "transaction_id": None,
                        "customer_id": member["customer_id"],
                        "amount": amount,
                        "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "coupon_id": coupon_applied["coupon_id"] if coupon_applied else None,
                        "product_id": product["product_id"],
                        "payment_method": payment_method
                    })
                    
    return rings_customers, rings_transactions, rings_referrals
