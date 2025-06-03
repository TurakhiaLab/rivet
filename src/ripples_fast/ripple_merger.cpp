#include "ripples.hpp"
#include "src/mutation_annotated_tree.hpp"
#include <algorithm>
#include <cassert>
#include <csignal>
#include <cstddef>
#include <functional>
#include <iostream>
#include <limits>
#include <stdio.h>
#include <string>
#include <string_view>
#include <tbb/concurrent_unordered_set.h>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>
#ifdef __SSE2__
#include <emmintrin.h>
typedef unsigned short __v8hu __attribute__((__vector_size__(16)));
typedef  short __v8h __attribute__((__vector_size__(16)));
typedef  int __v4i __attribute__((__vector_size__(16)));
typedef char __v16b __attribute__((__vector_size__(16)));
typedef unsigned short __v8hu_u __attribute__((__vector_size__(16), __aligned__(1)));
#endif
#define DIAGNOSTICS
static int acceptor (const Mut_Count_Out_t &counts, size_t i, size_t j,
                     size_t curr_node_idx, size_t node_size,
                     size_t num_mutations) {
    auto first_half_mut =
        counts[i * node_size + curr_node_idx].count_before_exclusive();
    auto second_half_mut = counts[num_mutations * node_size + curr_node_idx]
                           .count_before_exclusive() -
                           counts[(j - 1) * node_size + curr_node_idx]
                           .count_before_inclusive();
    return first_half_mut + second_half_mut;
}
static int donor(const Mut_Count_Out_t &counts, size_t i, size_t j,
                 size_t curr_node_idx, size_t node_size,
                 size_t num_mutations) {
    return counts[(j - 1) * node_size + curr_node_idx]
           .count_before_inclusive() -
           (counts[i * node_size + curr_node_idx].count_before_exclusive());
}

#ifdef __SSE2__
static void push_val(std::vector<int> &filtered_idx,
                     std::vector<unsigned short>& filtered_par_score,
                     int start_idx, int mask, __v8hu par_score) {
    for (int indi_idx = 0; indi_idx < 8; indi_idx++) {
        if (mask & (1 << (2 * indi_idx))) {
            filtered_idx.push_back(start_idx + indi_idx);
            filtered_par_score.push_back(par_score[indi_idx]);
        }
    }
}
template<typename T1,typename T2>
struct std::hash<std::pair<T1, T2>>{
    size_t operator()(const std::pair<T1, T2>& in) const{
        size_t seed=0;
        boost::hash_combine(seed, in.first);
        boost::hash_combine(seed, in.second);
        return seed;
    }
};
static unsigned short min_8(__v8h in) {
    __v8h temp1=(__v8h)__builtin_ia32_pshufd((__v4i)in,0x4e);
    auto min1=__builtin_ia32_pminsw128(temp1,in);
    temp1=__builtin_ia32_pshuflw(min1,0x4e);
    min1=__builtin_ia32_pminsw128(temp1,min1);
    temp1=__builtin_ia32_pshuflw(min1,0xb1);
    min1=__builtin_ia32_pminsw128(temp1,min1);
    auto out=min1[0];
#ifndef NDEBUG
    unsigned short test=in[0];
    for (int i=0; i<8; i++) {
        test=std::min((unsigned short)in[i],test);
    }
    assert(test==out);
#endif
    return out;
}
#endif
static int min_parsimony(const Ripples_Mapper_Output_Interface &out_ifc,size_t node_size, size_t num_mutations, size_t skip_start_idx, size_t skip_end_idx){
    unsigned short cur_min=std::numeric_limits<unsigned short>::max();

    for (size_t node_idx=0; node_idx<skip_start_idx; node_idx++) {
        cur_min=std::min(cur_min,out_ifc.mut_count_out[node_size*num_mutations+node_idx].count_before_exclusive());
    }
    for (size_t node_idx=skip_end_idx; node_idx<node_size; node_idx++) {
        cur_min=std::min(cur_min,out_ifc.mut_count_out[node_size*num_mutations+node_idx].count_before_exclusive());
    }
    return cur_min;
}
static std::pair<int,int> filter(const Ripples_Mapper_Output_Interface &out_ifc, size_t i,
                                 size_t j, size_t node_size, size_t num_mutations,
                                 int idx_start,int idx_end,
                                 std::vector<int> &donor_filtered_idx,
                                 std::vector<unsigned short> &donor_filtered_par_score,
                                 std::vector<int> &acceptor_filtered_idx,
                                 std::vector<unsigned short> &acceptor_filtered_par_score,
                                 int pasimony_threshold) {
    #ifndef __SSE2__
    int donor_min_par = pasimony_threshold + 1;
    int acceptor_min_par = pasimony_threshold + 1;
    const auto& counts = out_ifc.mut_count_out;
    for (; idx_start < idx_end;
         idx_start++) {
        auto donor_par =
            donor(counts, i, j, idx_start, node_size, num_mutations);
        auto acceptor_par =
            acceptor(counts, i, j, idx_start, node_size, num_mutations);

        if (donor_par <= pasimony_threshold) {
            donor_min_par = std::min(donor_min_par, donor_par);
            donor_filtered_idx.push_back(idx_start);
            donor_filtered_par_score.push_back(donor_par);
        }
        if (acceptor_par <= pasimony_threshold) {
            acceptor_min_par = std::min(acceptor_min_par, acceptor_par);
            acceptor_filtered_idx.push_back(idx_start);
            acceptor_filtered_par_score.push_back(acceptor_par);
        }
    }
    #else
#ifndef NDEBUG
    int donor_par_min_debug= pasimony_threshold + 1;
    int acceptor_par_min_debug= pasimony_threshold + 1;
    std::vector<int> donor_idx_debug(donor_filtered_idx);
    std::vector<int> acceptor_idx_debug(acceptor_filtered_idx);
#endif
    unsigned short threshold_par = pasimony_threshold + 1;
    __v8hu load_cmp_mask= {1,2,3,4,5,6,7,8};
    __v8hu threshold_par_vec=threshold_par-(__v8hu) {};
    __v8h donor_min_par_vec=(__v8h)threshold_par_vec;
    __v8h acceptor_min_par_vec=(__v8h)threshold_par_vec;

    const auto& counts = out_ifc.mut_count_out;
    const auto* base_i_offset=counts.data()+i*node_size;
    const auto* base_j_offset=counts.data()+(j - 1) * node_size;
    const auto* base_all_mut_offset=counts.data()+num_mutations*node_size;
    __v8hu exlusive_count_extract_mask=0x7fff-(__v8hu) {};
    //__m128i_u inclusive_extract_mask=_mm_set1_epi16(0x8000);
    for (; idx_start < (idx_end-8);
            idx_start+=8) {
        __v8hu first_half_raw=*(__v8hu_u*)(base_i_offset+idx_start);
        __v8hu first_half_exclusive=exlusive_count_extract_mask&first_half_raw;
        __v8hu all_muts_raw=*((__v8hu_u*)(base_all_mut_offset+idx_start));
        __v8hu all_muts=exlusive_count_extract_mask& all_muts_raw;
        __v8hu second_half_before_raw=*((__v8hu_u*)(base_j_offset+idx_start));
        __v8hu second_half_before_included_flag=(second_half_before_raw>>15);
        __v8hu second_half_before_inclusive=(second_half_before_raw&exlusive_count_extract_mask)+ second_half_before_included_flag;
        __v8hu acceptor_par=all_muts-second_half_before_inclusive+first_half_exclusive;
        __v8hu donor_par=second_half_before_inclusive-first_half_exclusive;
        int donor_pass=__builtin_ia32_pmovmskb128((__v16b)(donor_par<threshold_par_vec));
        int acceptor_pass=__builtin_ia32_pmovmskb128((__v16b)(acceptor_par<threshold_par_vec));
#ifndef NDEBUG
        auto end_idx=std::min(8,idx_end-idx_start);
        for (int indi_idx=0; indi_idx<end_idx; indi_idx++) {
            auto donor_par_i =
                donor(counts, i, j, idx_start+indi_idx, node_size, num_mutations);
            auto acceptor_par_i =
                acceptor(counts, i, j, idx_start+indi_idx, node_size, num_mutations);
            if (donor_par_i<=pasimony_threshold) {
                donor_idx_debug.push_back(idx_start+indi_idx);
            }
            if (acceptor_par_i<=pasimony_threshold) {
                acceptor_idx_debug.push_back(idx_start+indi_idx);
            }
            assert(donor_par_i==donor_par[indi_idx]);
            assert(acceptor_par_i==acceptor_par[indi_idx]);
            assert((donor_par_i<=pasimony_threshold)==((donor_pass&(1<<(2*indi_idx)))!=0));
            assert((acceptor_par_i<=pasimony_threshold)==((acceptor_pass&(1<<(2*indi_idx)))!=0));
            donor_par_min_debug=std::min(donor_par_min_debug,(int)donor_par_i);
            acceptor_par_min_debug=std::min(acceptor_par_min_debug,(int)acceptor_par_i);
        }
        for (; end_idx<8; end_idx++) {
            assert(donor_par[end_idx]==0x7fff);
            assert(acceptor_par[end_idx]==0x7fff);
        }
#endif
        if (donor_pass) {
            push_val(donor_filtered_idx, donor_filtered_par_score, idx_start, donor_pass, donor_par);
            donor_min_par_vec=__builtin_ia32_pminsw128(donor_min_par_vec,(__v8h)donor_par);
        }
        if (acceptor_pass) {
            push_val(acceptor_filtered_idx, acceptor_filtered_par_score, idx_start, acceptor_pass, acceptor_par);
            acceptor_min_par_vec=__builtin_ia32_pminsw128(acceptor_min_par_vec,(__v8h)acceptor_par);
        }
        assert(donor_idx_debug.size()==donor_filtered_idx.size());
        assert(acceptor_idx_debug.size()==acceptor_filtered_idx.size());
    }
    __v8hu first_half_raw=*(__v8hu_u*)(base_i_offset+idx_start);
    __v8hu first_half_exclusive=exlusive_count_extract_mask&first_half_raw;
    __v8hu all_muts_raw=*((__v8hu_u*)(base_all_mut_offset+idx_start));
    __v8hu all_muts=exlusive_count_extract_mask& all_muts_raw;
    __v8hu second_half_before_raw=*((__v8hu_u*)(base_j_offset+idx_start));
    __v8hu second_half_before_included_flag=(second_half_before_raw>>15);
    __v8hu second_half_before_inclusive=(second_half_before_raw&exlusive_count_extract_mask)+ second_half_before_included_flag;
    __v8hu acceptor_par=all_muts-second_half_before_inclusive+first_half_exclusive;
    __v8hu donor_par=second_half_before_inclusive-first_half_exclusive;
    __v8hu load_mask=load_cmp_mask>((unsigned short)(idx_end-idx_start))-(__v8hu) {};
    load_mask>>=1;
    acceptor_par|=load_mask;
    acceptor_par&=exlusive_count_extract_mask;
    donor_par|=load_mask;
    donor_par&=exlusive_count_extract_mask;
    int donor_pass=__builtin_ia32_pmovmskb128((__v16b)(donor_par<threshold_par_vec));
    int acceptor_pass=__builtin_ia32_pmovmskb128((__v16b)(acceptor_par<threshold_par_vec));
    if (donor_pass) {
        push_val(donor_filtered_idx, donor_filtered_par_score, idx_start, donor_pass, donor_par);
        donor_min_par_vec=__builtin_ia32_pminsw128(donor_min_par_vec,(__v8h)donor_par);
    }
    if (acceptor_pass) {
        push_val(acceptor_filtered_idx, acceptor_filtered_par_score, idx_start, acceptor_pass, acceptor_par);
        acceptor_min_par_vec=__builtin_ia32_pminsw128(acceptor_min_par_vec,(__v8h)acceptor_par);
    }
    auto donor_min_par=min_8(donor_min_par_vec);
    auto acceptor_min_par=min_8(acceptor_min_par_vec);
    assert(donor_min_par==donor_par_min_debug);
    assert(acceptor_min_par==acceptor_par_min_debug);
    #endif
    return std::make_pair(donor_min_par,acceptor_min_par);
}
static void threshold_parsimony(const Ripples_Mapper_Output_Interface &out_ifc,
                                size_t node_size, size_t num_mutations,
                                std::vector<int> &idx,
                                std::vector<unsigned short> &par_score,
                                std::vector<Recomb_Node> &filtered,
                                int pasimony_threshold,
                                const std::vector<MAT::Node*>& nodes_to_search) {
    const auto& counts = out_ifc.mut_count_out;
    for (size_t filtered_idx = 0; filtered_idx < idx.size(); filtered_idx++) {
        if (par_score[filtered_idx] <= pasimony_threshold) {
            auto idx_start = idx[filtered_idx];
            filtered.emplace_back(nodes_to_search[idx_start],
                                  counts[node_size * num_mutations + idx_start]
                                  .count_before_exclusive(),
                                  par_score[filtered_idx],
                                  out_ifc.is_sibling[idx_start]);
        }
    }
}
enum Node_Type{DONOR,ACCEPTOR,RECOMB};
struct Merging_Nuc_Type{
    int position;
    char nuc;
    char ref_nuc;
    char par_nuc;
    Node_Type node_Type;
};
typedef std::unordered_map<int, Merging_Nuc_Type> Mut_Map_T;
static void gather_mutations(Mut_Map_T& mutations, Node_Type node_type,const MAT::Node* node,bool track_par_nuc){
    if(!node){
        return;
    }
    for (const auto& mut : node->mutations) {
        mutations.emplace(mut.position,Merging_Nuc_Type{mut.position,mut.mut_nuc,mut.ref_nuc,track_par_nuc?mut.par_nuc:mut.mut_nuc ,node_type});
    }
    gather_mutations(mutations, node_type, node->parent,false);
}
static void fill_muts(std::vector<Merging_Nuc_Type>& to_fill, const Mut_Map_T& filler){
    for (const auto& mut : filler) {
        if ((mut.second.nuc!=mut.second.ref_nuc)||mut.second.par_nuc) {
            to_fill.push_back(mut.second);
        }
    }
}
std::vector<Merging_Nuc_Type> merge_nuc(const MAT::Node* acceptor,const MAT::Node* donor, const std::vector<MAT::Mutation>& recomb_muts){
    Mut_Map_T accptor_muts;
    gather_mutations(accptor_muts, ACCEPTOR, acceptor,true);
    Mut_Map_T donor_muts;
    gather_mutations(donor_muts, DONOR, donor,true);
    std::vector<Merging_Nuc_Type> ret_val;
    ret_val.reserve(accptor_muts.size()+donor_muts.size()+recomb_muts.size());
    for (const auto& mut : recomb_muts) {
        if (mut.mut_nuc!=mut.ref_nuc) {
            ret_val.push_back(Merging_Nuc_Type{mut.position,mut.mut_nuc,mut.ref_nuc,mut.mut_nuc,RECOMB});
        }
    }
    fill_muts(ret_val, accptor_muts);
    fill_muts(ret_val, donor_muts);
    std::sort(ret_val.begin(),ret_val.end(),[](const Merging_Nuc_Type& l,const Merging_Nuc_Type& r){
        return l.position<r.position;
    });
    return ret_val;
}
/*struct Searched_Pairs{
    const MAT::Node* node_a;
    const MAT::Node* node_b;
    bool operator==(const Searched_Pairs& other){
        return (node_a==other.node_a&&node_b==other.node_b)
            ||(node_a==other.node_b&&node_b==other.node_a);
    }
};
template<>
struct std::hash<Searched_Pairs>{
    size_t operator()(const Searched_Pairs& in) const{
        return std::hash<const MAT::Node*>()(in.node_a)^std::hash<const MAT::Node*>()(in.node_b);
    }
};*/
typedef std::pair<const MAT::Node*, const MAT::Node*> Searched_Pairs ;
enum Informative_Type:int {NO_MATCH=0,MATCH_DONOR=1,MATCH_ACCEPTOR=2,MATCH_BOTH=3};
std::string to_string(Informative_Type in){
    switch (in) {
        case MATCH_ACCEPTOR:return "MATCH_ACCEPTOR";
        case MATCH_DONOR:return "MATCH_DONOR";
        case MATCH_BOTH:return "MATCH_BOTH";
        case NO_MATCH:return "NO_MATCH";
    }
    return "ERR";
}
/*struct Cnt_Type{
    int cnt[2];
    Cnt_Type(){
        cnt[0]=1;
        cnt[1]=1;
    }
    int& operator[](Informative_Type type){
        return cnt[type-1];
    }
    int operator[](Informative_Type type) const{
        return cnt[type-1];
    }
};*/
struct Change_Point{
    int interval_start;
    int interval_end;
    //Cnt_Type prev_cnt;
    int prev_acceptor_match;
    int prev_donor_match;
    Informative_Type end_inf_type;
};
struct Change_Point_Finder_State{
    int uncorrectable;
    //Cnt_Type prev_cnt;
    int prev_acceptor_match;
    int prev_donor_match;
    int prev_informative_pos;
    Informative_Type cur_informative_type; //place holder for first;
    Informative_Type init_informative_type; //place holder for first;
    std::vector<Change_Point> change_points;
    #ifdef DIAGNOSTICS
    std::string diagnoistic_string;
    #endif
    Change_Point_Finder_State():uncorrectable(0),prev_acceptor_match(0),prev_donor_match(0),prev_informative_pos(0),cur_informative_type(NO_MATCH),init_informative_type(NO_MATCH){
    }
};
static Informative_Type get_informative_type(char *nuc){
    return Informative_Type{(nuc[RECOMB]==nuc[DONOR])|((nuc[RECOMB]==nuc[ACCEPTOR])<<1)};
}
static void change_point_finder(Change_Point_Finder_State& state, int prev_pos, char* nuc,char* par_nuc){
    if (prev_pos==-1) {
        return;
    }
    auto this_informative_type=get_informative_type(nuc);
    auto par_informative_type=get_informative_type(par_nuc);
    this_informative_type=Informative_Type(this_informative_type|par_informative_type);
    if ((this_informative_type==MATCH_DONOR||this_informative_type==MATCH_ACCEPTOR)) {
        if (state.cur_informative_type==NO_MATCH) {
            state.init_informative_type=this_informative_type;
        }else if (this_informative_type!=state.cur_informative_type) {
            state.change_points.push_back(Change_Point{
                state.prev_informative_pos,
                prev_pos,
                state.prev_acceptor_match,
                state.prev_donor_match,
                this_informative_type});
        }
        state.prev_informative_pos=prev_pos;
        state.cur_informative_type=this_informative_type;
    }
    switch (this_informative_type) {
        case MATCH_ACCEPTOR: state.prev_acceptor_match++; break;
        case MATCH_DONOR: state.prev_donor_match++; break;
        case NO_MATCH:state.uncorrectable++; break;
        default: ;
    }
    #ifdef DIAGNOSTICS
    state.diagnoistic_string+=(
        std::to_string(prev_pos)+'\t'+
        MAT::get_nuc(nuc[DONOR])+'\t'+
        MAT::get_nuc(nuc[ACCEPTOR])+'\t'+
        MAT::get_nuc(nuc[RECOMB])+'\t'+
        MAT::get_nuc(par_nuc[DONOR])+'\t'+
        MAT::get_nuc(par_nuc[ACCEPTOR])+'\t'+
        to_string(this_informative_type)+'\n'
    );
    #endif
}
struct Valid_Pair_Outputter{
    tbb::concurrent_vector<Recomb_Interval> &valid_pairs;
    const Recomb_Node& acceptor_node;
    const Recomb_Node& donor_node;
    int threshold;
    int non_correctable;
    #ifdef DIAGNOSTICS
    std::string& diagnoistic_string;
    #endif
    bool operator()(const Change_Point& acc_to_don,
        const Change_Point& don_to_acc, int par_score){
        if (par_score<=threshold) {
            valid_pairs.push_back(
                    Recomb_Interval(donor_node, acceptor_node, acc_to_don.interval_start, acc_to_don.interval_end,
                                    don_to_acc.interval_start,don_to_acc.interval_end,non_correctable+par_score));
                    diagnoistic_string=diagnoistic_string+
                        "start_low"+std::to_string(acc_to_don.interval_start)+
                        "start_high"+std::to_string(acc_to_don.interval_end)+
                        "end_low"+std::to_string(don_to_acc.interval_start)+
                        "end_high"+std::to_string(don_to_acc.interval_end)+"\n";
            return true;
        }
        return false;
    }
    bool donor_to_acceptor(const Change_Point& don_to_acc, int par_score){
        if (par_score<=threshold) {
            valid_pairs.push_back(
                    Recomb_Interval(acceptor_node,donor_node, 
                                    don_to_acc.interval_start,don_to_acc.interval_end,1e9,1e9,non_correctable+par_score));
                    diagnoistic_string=diagnoistic_string+
                        "end_low"+std::to_string(don_to_acc.interval_start)+
                        "end_high"+std::to_string(don_to_acc.interval_end)+"\n";
            return true;
        }
        return false;
    }
};
static bool compute_break_points(const std::vector<Change_Point>& change_point,
    int final_acceptor_match,
    int final_donor_match,
    Valid_Pair_Outputter& output
    ){
    bool found=false;
    Change_Point null_end_interval;
    null_end_interval.interval_end=1e9;
    null_end_interval.interval_start=1e9;
    //single donor to acceptor
    for (const auto& point :change_point) {
        if (point.end_inf_type==MATCH_ACCEPTOR) {
            auto donor_seg_par=point.prev_acceptor_match;
            auto acceptor_seg_par=final_donor_match-point.prev_donor_match;
            found|=output.donor_to_acceptor(point, donor_seg_par+acceptor_seg_par);        
        }
    }
    for(size_t start_idx=0;start_idx<change_point.size();start_idx++){
        if (change_point[start_idx].end_inf_type==MATCH_DONOR) {
            //Sites that match neither of the acceptor or donor are already excluded from threshold
            //Then the "mutation count" before first breakpoint is the number of mutations that only match donor
            int mut_count=change_point[start_idx].prev_donor_match;
            //single acceptor to donor break point
            found|=output(change_point[start_idx],null_end_interval,mut_count+final_acceptor_match-change_point[start_idx].prev_acceptor_match);
            if (mut_count>output.threshold) {
                break;
            }
            for (size_t end_idx=start_idx+1; end_idx<change_point.size(); end_idx++) {
                if (change_point[end_idx].end_inf_type==MATCH_ACCEPTOR) {
                    auto donor_seg_par=change_point[end_idx].prev_acceptor_match-change_point[start_idx].prev_acceptor_match;
                    auto second_acc_seg_par=final_donor_match-change_point[end_idx].prev_donor_match;
                    found|=output(change_point[start_idx],change_point[end_idx],mut_count+second_acc_seg_par+donor_seg_par);
                }
            }
        }
    }
    return found;
}
static void
find_pairs(const std::vector<Recomb_Node> &donor_nodes,
           const std::vector<Recomb_Node> &acceptor_nodes,
           const std::vector<MAT::Mutation> &pruned_sample_mutations, int i,
           int j, int parsimony_threshold, const MAT::Tree &T,
           tbb::concurrent_vector<Recomb_Interval> &valid_pairs,const MAT::Node* recomb_node,
           tbb::concurrent_unordered_set<Searched_Pairs>& searched_pairs) {
    bool has_printed = false;

    for (auto d : donor_nodes) {
        /*if (T.is_ancestor(nid_to_consider, d.name)) {
            //raise(SIGTRAP);
            continue;
        }*/
        for (auto a : acceptor_nodes) {
            /*if (T.is_ancestor(nid_to_consider, a.name)) {
                //raise(SIGTRAP);
                continue;
            }*/
            // Ensure donor and acceptor are not the same and
            // neither of them is a descendant of the recombinant
            // node total parsimony is less than the maximum allowed
            if (parsimony_threshold < d.parsimony + a.parsimony) {
                break;
            }
            if (d.node != a.node) {
                auto emplace_res=searched_pairs.emplace(d.node,a.node);
                if (!emplace_res.second) {
                    //the pair have been searched
                    return;
                }
                Change_Point_Finder_State state;
                #ifdef DIAGNOSTICS
                state.diagnoistic_string="donor:"+d.node->identifier+", acceptor:"+a.node->identifier+"recomb_node:"+recomb_node->identifier+"threshold:"+std::to_string(parsimony_threshold)+
                    "\nposition\tdonor\tacceptor\trecomb\tdonor_par\tacceptor_par\tinformative_type\n";
                #endif
                auto muts = merge_nuc(a.node, d.node, pruned_sample_mutations);
                int prev_pos= -1;
                char nuc[]={0,0,0};
                char par_nuc[]={0,0,0};

                for (const auto &mut : muts) {
                    if (mut.position != prev_pos) {
                        change_point_finder(state, prev_pos, nuc, par_nuc);
                        for (int type_idx = 0; type_idx < 3; type_idx++) {
                            nuc[type_idx] = mut.ref_nuc;
                            par_nuc[type_idx]=mut.ref_nuc;   
                        }
                        prev_pos=mut.position;
                    }
                    nuc[mut.node_Type]=mut.nuc;
                    par_nuc[mut.node_Type]=mut.par_nuc;
                }
                change_point_finder(state, prev_pos, nuc, par_nuc);
                Valid_Pair_Outputter output{
                    valid_pairs,
                    a,
                    d,
                    parsimony_threshold-state.uncorrectable,
                    state.uncorrectable,
                    state.diagnoistic_string
                };
                #ifdef DIAGNOSTICS
                state.diagnoistic_string+=("uncorrectable:"+std::to_string(state.uncorrectable)+"\n");
                #endif
                auto found=compute_break_points(state.change_points, 
                state.prev_acceptor_match, 
                state.prev_donor_match, 
                output);
                #ifdef DIAGNOSTICS
                if (!found) {
                    fprintf(stderr, "===NOT FOUND===\n%s===NOT FOUND END====\n",state.diagnoistic_string.c_str());
                }
                puts(state.diagnoistic_string.c_str());
                #endif
                has_printed=true;
                break;
            }
        }
        if (has_printed) {
            break;
        }
    }
}
struct check_breakpoint {
    const Ripples_Mapper_Output_Interface &out_ifc;
    const std::vector<MAT::Mutation> &pruned_sample_mutations;
    tbb::concurrent_unordered_set<Searched_Pairs>& all_searched_pairs;
    int skip_start_idx;
    int skip_end_idx;
    size_t node_size;
    int pasimony_threshold;
    const std::vector<MAT::Node *> &nodes_to_search;
    const MAT::Tree &T;
    tbb::concurrent_vector<Recomb_Interval> &valid_pairs;
    const MAT::Node* recomb_node;
    void operator()(std::pair<int,int> in) const {
        int i=in.first;
        int j=in.second;
        if (i==2&&j==14) {
            //raise(SIGTRAP);
        }

        size_t num_mutations = pruned_sample_mutations.size();
        std::vector<int> donor_filtered_idx;
        std::vector<unsigned short> donor_filtered_par_score;
        std::vector<int> acceptor_filtered_idx;
        std::vector<unsigned short> acceptor_filtered_par_score;
        donor_filtered_idx.reserve(nodes_to_search.size());
        donor_filtered_par_score.reserve(nodes_to_search.size());
        acceptor_filtered_idx.reserve(nodes_to_search.size());
        acceptor_filtered_par_score.reserve(nodes_to_search.size());
        auto min_first = filter(
                             out_ifc, i, j, node_size, num_mutations, 0, skip_start_idx,
                             donor_filtered_idx, donor_filtered_par_score, acceptor_filtered_idx,
                             acceptor_filtered_par_score, pasimony_threshold);
        auto min_second = filter(
                              out_ifc, i, j, node_size, num_mutations, skip_end_idx,
                              nodes_to_search.size(), donor_filtered_idx,
                              donor_filtered_par_score, acceptor_filtered_idx,
                              acceptor_filtered_par_score, pasimony_threshold);
        auto donor_min = std::min(min_first.first, min_second.first);
        auto acceptor_min=std::min(min_first.second,min_second.second);
        if (acceptor_min+donor_min>pasimony_threshold) {
            return;
        }
        std::vector<Recomb_Node> donor_filtered;
        std::vector<Recomb_Node> acceptor_filtered;
        donor_filtered.reserve(donor_filtered_idx.size());
        acceptor_filtered.reserve(donor_filtered_idx.size());
        threshold_parsimony(out_ifc, node_size, num_mutations,
                            donor_filtered_idx, donor_filtered_par_score,
                            donor_filtered, pasimony_threshold - acceptor_min,
                            nodes_to_search);
        threshold_parsimony(out_ifc, node_size, num_mutations,
                            acceptor_filtered_idx, acceptor_filtered_par_score,
                            acceptor_filtered, pasimony_threshold - donor_min,
                            nodes_to_search);
        std::sort(acceptor_filtered.begin(), acceptor_filtered.end());
        std::sort(donor_filtered.begin(), donor_filtered.end());
        find_pairs(donor_filtered, acceptor_filtered, pruned_sample_mutations,
                   i, j, pasimony_threshold, T, valid_pairs,recomb_node,all_searched_pairs);
    }
};

struct search_position {
    const std::vector<MAT::Mutation> &pruned_sample_mutations;
    int &i;
    int &j;
    int branch_len;
    int min_range;
    int max_range;
    int last_i;
    bool is_j_end_of_range(int start_range_high, int total_size) const {
        return j >= total_size || total_size - (j - i) < branch_len ||
               pruned_sample_mutations[j-1].position - start_range_high >
               max_range;
    }
    std::pair<int, int> operator()(tbb::flow_control &fc) const {
        int start_range_high=0;// = pruned_sample_mutations[i].position;
        int total_size = pruned_sample_mutations.size();
        // i end
        if (i > last_i) {
            fc.stop();
            return std::make_pair(0, 0);
        }
        j++;
        // j end
        if (i!=-1) {
            start_range_high = pruned_sample_mutations[i].position;
        }

        while (i==-1||is_j_end_of_range(start_range_high, total_size)) {
            i++;
            if (i > last_i) {
                fc.stop();
                return std::make_pair(0, 0);
            }
            start_range_high = pruned_sample_mutations[i].position;
            j = i + branch_len;
            while (j < total_size && pruned_sample_mutations[j - 1].position <
                    start_range_high + min_range) {
                j++;
            }
        }
        return std::make_pair(i, j);
    }
};

int ripplrs_merger(const Pruned_Sample &pruned_sample,
                    const std::vector<int> & idx_map,
                    const std::vector<MAT::Node *> &nodes_to_search,
                    int pasimony_threshold,
                    const MAT::Tree &T,
                    tbb::concurrent_vector<Recomb_Interval> &valid_pairs,
                    const Ripples_Mapper_Output_Interface &out_ifc,
                    int nthreads, int branch_len, int min_range,
                    int max_range,int min_improvement) {
    const auto &sample_mutations = pruned_sample.sample_mutations;
    auto pruned_node = pruned_sample.sample_name;
    auto node_size=nodes_to_search.size();
        int skip_start_idx=std::abs(idx_map[pruned_node->dfs_idx]);
    //The next index after the one corresponding to dfs_idx -1
    int skip_end_idx=std::abs(idx_map[pruned_node->dfs_end_idx]);
    int actual_min_pars=min_parsimony(out_ifc, node_size, sample_mutations.size(),skip_start_idx,skip_end_idx);
    auto actual_threshold=actual_min_pars-min_improvement;
    if (actual_threshold<pasimony_threshold) {
        fprintf(stderr, "%s\t%d\t%d\n",
        pruned_sample.sample_name->identifier.c_str(),
        pasimony_threshold,
        actual_threshold);
        pasimony_threshold=actual_threshold;
        if (pasimony_threshold<0) {
            return actual_min_pars;
        }
    }else if(actual_threshold>pasimony_threshold) {
        fprintf(stderr, "ERROR:%s,old thresh%d new_thresh%d\n",pruned_sample.sample_name->identifier.c_str(),pasimony_threshold,actual_min_pars);
    }

    int i = -1;
    int j = 0;
    const auto last_pos = sample_mutations.back().position - min_range;
    int last_i = sample_mutations.size() - branch_len;
    while (last_i > 0 && sample_mutations[last_i].position > last_pos) {
        last_i--;
    }
    tbb::concurrent_unordered_set<Searched_Pairs> all_searched_pairs;
    tbb::parallel_pipeline(
        nthreads + 1,
        tbb::make_filter<void, std::pair<int, int>>(
            tbb::filter::serial_in_order,
            search_position{sample_mutations, i, j, branch_len, min_range,
                            max_range, last_i}) &
        tbb::make_filter<std::pair<int, int>, void>(
            tbb::filter::parallel,
            check_breakpoint{out_ifc, sample_mutations,all_searched_pairs,
                             skip_start_idx,skip_end_idx,
                             node_size, pasimony_threshold,
                             nodes_to_search, T, valid_pairs,pruned_node
                             })

    );
    return actual_min_pars;
}